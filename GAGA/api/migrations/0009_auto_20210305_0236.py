# Generated by Django 3.1.5 on 2021-03-05 02:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_commentfilter'),
    ]

    operations = [
        migrations.AddField(
            model_name='promo_account',
            name='comment_level',
            field=models.IntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(15)]),
        ),
        migrations.AddField(
            model_name='promo_account',
            name='increment_comment_level_comment_delta',
            field=models.IntegerField(default=400, validators=[django.core.validators.MinValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='promo_account',
            name='increment_comment_level_comment_number',
            field=models.IntegerField(default=400),
        ),
    ]
