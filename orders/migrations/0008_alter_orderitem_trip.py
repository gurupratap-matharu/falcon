# Generated by Django 5.0.3 on 2024-08-02 22:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0007_alter_order_options_alter_orderitem_options_and_more"),
        ("trips", "0024_remove_trip_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="trip",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_items",
                to="trips.trip",
            ),
        ),
    ]