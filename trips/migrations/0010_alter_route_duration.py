# Generated by Django 5.0.3 on 2024-05-31 16:11

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0009_route_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="route",
            name="duration",
            field=models.FloatField(
                default=3.5,
                validators=[
                    django.core.validators.MinValueValidator(0.1),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name="Duration in Hours",
            ),
        ),
    ]