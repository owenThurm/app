# Generated by Django 3.1.5 on 2021-03-07 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_promo_account_is_resting'),
    ]

    operations = [
        migrations.AddField(
            model_name='promo_account',
            name='using_comment_filter',
            field=models.BooleanField(default=True),
        ),
    ]
