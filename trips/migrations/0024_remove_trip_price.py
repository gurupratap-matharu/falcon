# Generated by Django 5.0.3 on 2024-07-28 19:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0023_trip_category"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="trip",
            name="price",
        ),
    ]
