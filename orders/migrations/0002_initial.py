# Generated by Django 4.1.5 on 2023-02-06 17:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("orders", "0001_initial"),
        ("trips", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="trip",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="order_items",
                to="trips.trip",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="passengers",
            field=models.ManyToManyField(related_name="orders", to="orders.passenger"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["-created_on"], name="orders_orde_created_3fff13_idx"
            ),
        ),
    ]