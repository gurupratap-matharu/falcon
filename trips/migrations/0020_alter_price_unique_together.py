# Generated by Django 5.0.3 on 2024-07-26 16:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0019_price"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="price",
            unique_together={("route", "origin", "destination")},
        ),
    ]
