# Generated by Django 5.0.3 on 2024-07-06 18:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0014_alter_trip_schedule"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="stop",
            name="arrival",
        ),
        migrations.RemoveField(
            model_name="stop",
            name="departure",
        ),
    ]