# Generated by Django 4.1.5 on 2023-02-01 18:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0005_remove_seat_price_trip_price"),
        ("orders", "0003_remove_passenger_order_item_passenger_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="passenger",
            name="trip",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="passengers",
                to="trips.trip",
            ),
        ),
    ]
