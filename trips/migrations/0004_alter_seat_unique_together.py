# Generated by Django 4.2.2 on 2023-07-14 16:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0003_alter_trip_options"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="seat",
            unique_together={("trip", "seat_number")},
        ),
    ]