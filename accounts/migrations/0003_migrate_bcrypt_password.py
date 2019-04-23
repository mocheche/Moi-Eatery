from django.db import migrations

from ..hashers import PBKDF2WrappedBCryptSHA256PasswordHasher

def forwards_func(apps,shema_edit):
    User = apps.get_model('auth','User')
    users = User.objects.filter(password__startswith('bcry'))
    hashers = PBKDF2WrappedBCryptSHA256PasswordHasher()

    for user in users:
        algorithm, salt ,bcrypt = user.password.split("$",2)
        user.password = hashers.encode_bcrypt_sha256(bcrypt, salt)
        user.save(upadate_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('accounts', '0002_auto_20190416_1640'),
    ]

    operations = [
                  migrations.RunPython(forwards_func)
                  ]