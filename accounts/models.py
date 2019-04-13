import re
from django.shortcuts import reverse
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import send_mail
from datetime import timedelta
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import (AbstractBaseUser,  
                                        BaseUserManager )

from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator, ValidationError

#provides a default phone number frields for internationalization
from phonenumber_field.modelfields import PhoneNumberField
#

from Eatery.utils import unique_key_generator

#send_mail(subject, message, from_email, recipient_list, html_message)

DEFAULT_ACTIVATION_DAYS = getattr(settings, 'DEFAULT_ACTIVATION_DAYS', 7)

def validate_phone(value):
    string =  '^\+(?:[0-9].?)[0-9]{6,14}$'
    pat    = re.compile(string)
    value = str(value)
    if not pat.match(value):
        raise ValidationError(""
                              "Please provide a valid international telephone"
                              " number starting with the area code of your country")
def validate_card(number):
    'Validates any credit card number using LUHN method'
    number = re.sub(r' ', '', str(number))
    count = 0
    for i in range(len(number)):
        val = int(number[-(i+1)])
        if i % 2 == 0:
            count += val
        else:
            count += int(str(2 * val)[0])
            if val > 5:
                count += int(str(2 * val)[1])
    if not count % 10 == 0:
        raise ValidationError('Provide a valid Card number please')


def validate_id_number(value):
    string = r'^[0-9]{6,12}$'
    pat    = re.compile(string)
    value  = str(value)
    if not pat.match(value):
        raise ValidationError("ID Number must be between 6 and 12") 
    

class UserManager(BaseUserManager):
   use_in_migrations = True
    
   def create_user(self, email, password=None, is_active=True, is_staff=False, is_admin=False):
        if not email:
            raise ValueError("Users must have an email address")
        
        if not password:
            raise ValueError("Users must have a password")

        user_obj = self.model(
            email = self.normalize_email(email),

            )
        user_obj.set_password(password) # change user password
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.is_active = is_active
        user_obj.save(using=self._db)
        return user_obj

   def create_staffuser(self, email, password=None):
        user = self.create_user(
                email,
                password=password,
                is_staff=True
        )
        return user

   def create_superuser(self, email, password=None):
        user = self.create_user(
                email,
                password=password,
                is_staff=True,
                is_admin=True
        )
        return user

class User(AbstractBaseUser):
    email       = models.EmailField(max_length=255, unique=True)
    username   = models.CharField(max_length=255, blank=True)
    full_name   = models.CharField(max_length=255, blank=True)
    is_active   = models.BooleanField(default=True) # can login
    staff       = models.BooleanField(default=False) # staff user non superuser
    admin       = models.BooleanField(default=False) # superuser 
    timestamp   = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email' #username
    REQUIRED_FIELDS = []  

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        if self.full_name:
            return self.email
        return self.email

    def get_short_name(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        if self.is_admin:
            return True
        return self.staff

    @property
    def is_admin(self):
        return self.admin

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    # @property
    # def is_active(self):
    #     return self.active

class Profile(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    card       = models.CharField(max_length=20 , validators=[validate_card])
    id_number  = models.CharField(max_length=20, validators=[validate_id_number])
    address    = models.TextField()
    contact    = PhoneNumberField(validators=[validate_phone])




class EmailActivationQuerySet(models.query.QuerySet):
    def confirmable(self):
        now = timezone.now()
        start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
        # does my object have a timestamp in here
        end_range = now
        return self.filter(
                activated = False,
                forced_expired = False
              ).filter(
                timestamp__gt=start_range,
                timestamp__lte=end_range
              )


class EmailActivationManager(models.Manager):
    def get_queryset(self):
        return EmailActivationQuerySet(self.model, using=self._db)

    def confirmable(self):
        return self.get_queryset().confirmable()

    def email_exists(self, email):
        return self.get_queryset().filter(
                    Q(email=email) | 
                    Q(user__email=email)
                ).filter(
                    activated=False
                )


class EmailActivation(models.Model):
    user            = models.ForeignKey(User,on_delete=models.CASCADE)
    email           = models.EmailField()
    key             = models.CharField(max_length=120, blank=True, null=True)
    activated       = models.BooleanField(default=False)
    forced_expired  = models.BooleanField(default=False)
    expires         = models.IntegerField(default=7) # 7 Days
    timestamp       = models.DateTimeField(auto_now_add=True)
    update          = models.DateTimeField(auto_now=True)

    objects = EmailActivationManager()

    def __str__(self):
        return self.email

    def can_activate(self):
        qs = EmailActivation.objects.filter(pk=self.pk).confirmable() # 1 object
        if qs.exists():
            return True
        return False

    def activate(self):
        if self.can_activate():
            # pre activation user signal
            user = self.user
            user.is_active = True
            user.save()
            # post activation signal for user
            self.activated = True
            self.save()
            return True
        return False

    def regenerate(self):
        self.key = None
        self.save()
        if self.key is not None:
            return True
        return False
    
    def send_activation(self):
        if not self.activated and not self.forced_expired:
            if self.key:
                base_url = getattr(settings, 'BASE_URL', 'http://www.eatery.com:8000')
                key_path = reverse("account:email-activate", kwargs={'key': self.key}) # use reverse
                path = "{base}{path}".format(base=base_url, path=key_path)
                context = {
                    'path': path,
                    'email': self.email
                }
                txt_ = get_template("registration/emails/verify.txt").render(context)
                html_ = get_template("registration/emails/verify.html").render(context)
                subject = '1-Click Email Verification'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [self.email]
                sent_mail = send_mail(
                            subject,
                            txt_,
                            from_email,
                            recipient_list,
                            html_message=html_,
                            fail_silently=False,
                    )
                return sent_mail
        return False


def pre_save_email_activation(sender, instance, *args, **kwargs):
    if not instance.activated and not instance.forced_expired:
        if not instance.key:
            instance.key = unique_key_generator(instance)

pre_save.connect(pre_save_email_activation, sender=EmailActivation)


def post_save_user_create_receiver(sender, instance, created, *args, **kwargs):
    if created:
        obj = EmailActivation.objects.create(user=instance, email=instance.email)
        obj.send_activation()

post_save.connect(post_save_user_create_receiver, sender=User)



class GuestEmail(models.Model):
    email       = models.EmailField()
    active      = models.BooleanField(default=True)
    update      = models.DateTimeField(auto_now=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email