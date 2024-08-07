# Generated by Django 5.0.3 on 2024-08-03 16:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0009_orderitem_destination_orderitem_origin"),
        ("trips", "0024_remove_trip_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="seat",
            name="passenger",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="orders.passenger",
            ),
        ),
    ]
