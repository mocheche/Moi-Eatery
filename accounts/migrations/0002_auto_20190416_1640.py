# Generated by Django 2.1.7 on 2019-04-16 13:40

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='orders',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='total_sale',
        ),
    ]