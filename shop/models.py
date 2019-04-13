from django.shortcuts import reverse
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from Eatery.utils import unique_slug_generator
from django.conf import settings


class ProductQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(active=True)

    def featured(self):
        return self.filter(featured=True, active=True)

    def search(self, query):
        lookups = (Q(name__icontains=query) |
                  Q(description__icontains=query) |
                  Q(price__icontains=query) |
                  Q(slug__icontains=query)
                  )
        # tshirt, t-shirt, t shirt, red, green, blue,
        return self.filter(lookups).distinct()

class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset().active()

    def featured(self): #Product.objects.featured() 
        return self.get_queryset().featured()

    def get_by_id(self, id):
        qs = self.get_queryset().filter(id=id) # Product.objects == self.get_queryset()
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().active().search(query)


class Category(models.Model):
	name = models.CharField(max_length = 200, db_index = True)
	slug = models.SlugField(max_length  = 200, db_index = True, unique = True)
	class Meta:
		db_table            = 'category'
		ordering            = ('name',)
		verbose_name        = 'category'
		verbose_name_plural = 'categories'

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
	name  = models.CharField(max_length =  200 ,db_index = True)
	category   = models.ForeignKey(Category,related_name = 'products', on_delete = models.CASCADE)
	slug 	    = models.SlugField(max_length = 200  , db_index = True)
	image      = models.ImageField()
	description= models.TextField(blank=True)
	price      = models.DecimalField(max_digits= 20,decimal_places = 2)
	stock      = models.PositiveIntegerField()
	available  = models.BooleanField(default = True)
	created    = models.DateTimeField(auto_now_add = True)
	updated    = models.DateTimeField(auto_now = True)
	active     = models.BooleanField(default=True)
	
	objects = ProductManager()
	
	class Meta:
		db_table       = 'product'
		ordering       = ('name',)
		index_together = (('id','slug'),)


	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('shop:product_detail', args=[self.id,self.slug])
	
	def get_downloads(self):
		qs = self.productfile_set.all()
		return qs


def product_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

pre_save.connect(product_pre_save_receiver, sender=Product) 



