# Generated by Django 3.1.5 on 2021-02-20 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_resetpasswordtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='promo_account',
            name='is_liking',
            field=models.BooleanField(default=True),
        ),
    ]