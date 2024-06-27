# Generated by Django 5.0.3 on 2024-06-27 13:50

import django.core.validators
import django.db.models.deletion
import django_countries.fields
import trips.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("trips", "0001_initial"),
        ("trips", "0002_alter_trip_price"),
        ("trips", "0003_alter_trip_options"),
        ("trips", "0004_alter_seat_unique_together"),
        ("trips", "0005_alter_location_options_location_address_line1_and_more"),
        ("trips", "0006_alter_trip_destination_alter_trip_origin"),
        ("trips", "0007_route"),
        ("trips", "0008_stop"),
        ("trips", "0009_route_category"),
        ("trips", "0010_alter_route_duration"),
        ("trips", "0011_alter_location_options_alter_route_options_and_more"),
    ]

    initial = True

    dependencies = [
        ("companies", "0002_alter_company_options_alter_company_slug"),
        ("companies", "0005_alter_company_address_alter_company_description_and_more"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                (
                    "slug",
                    models.SlugField(max_length=200, unique=True, verbose_name="slug"),
                ),
                (
                    "abbr",
                    models.CharField(
                        blank=True,
                        help_text="Used internally as a reference",
                        max_length=7,
                        verbose_name="abbreviation",
                    ),
                ),
                (
                    "address_line1",
                    models.CharField(
                        blank=True, max_length=128, verbose_name="Address line 1"
                    ),
                ),
                (
                    "address_line2",
                    models.CharField(
                        blank=True, max_length=128, verbose_name="Address line 2"
                    ),
                ),
                (
                    "city",
                    models.CharField(blank=True, max_length=64, verbose_name="City"),
                ),
                (
                    "country",
                    django_countries.fields.CountryField(default="AR", max_length=2),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=9,
                        null=True,
                        verbose_name="Latitude",
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=9,
                        null=True,
                        verbose_name="Longitude",
                    ),
                ),
                (
                    "postal_code",
                    models.CharField(
                        blank=True, max_length=10, verbose_name="Postal Code"
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        blank=True, max_length=40, verbose_name="State/Province"
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "verbose_name": "location",
                "verbose_name_plural": "locations",
            },
        ),
        migrations.CreateModel(
            name="Seat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "seat_number",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(60),
                        ]
                    ),
                ),
                (
                    "seat_type",
                    models.CharField(
                        choices=[
                            ("C", "Cama"),
                            ("S", "Semicama"),
                            ("E", "Executive"),
                            ("O", "Other"),
                        ],
                        default="C",
                        max_length=1,
                    ),
                ),
                (
                    "seat_status",
                    models.CharField(
                        choices=[
                            ("A", "Available"),
                            ("B", "Booked"),
                            ("R", "Reserved"),
                            ("H", "Onhold"),
                        ],
                        default="A",
                        max_length=1,
                    ),
                ),
                (
                    "passenger",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seats",
                        to="orders.passenger",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Trip",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                ("slug", models.SlugField(max_length=200, verbose_name="slug")),
                (
                    "departure",
                    models.DateTimeField(verbose_name="Departure Date & Time"),
                ),
                ("arrival", models.DateTimeField(verbose_name="Arrival Date & Time")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="price",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("A", "Active"),
                            ("C", "Cancelled"),
                            ("H", "OnHold"),
                            ("D", "Delayed"),
                            ("O", "Other"),
                        ],
                        default="A",
                        max_length=2,
                        verbose_name="status",
                    ),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[("D", "Direct"), ("I", "Indirect"), ("O", "Other")],
                        default="D",
                        max_length=2,
                        verbose_name="mode",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to="trips/%Y/%m/%d", verbose_name="image"
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trips",
                        to="companies.company",
                    ),
                ),
                (
                    "destination",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="trips_inbound",
                        to="trips.location",
                    ),
                ),
                (
                    "orders",
                    models.ManyToManyField(
                        related_name="trips",
                        through="orders.OrderItem",
                        to="orders.order",
                    ),
                ),
                (
                    "origin",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="trips_outbound",
                        to="trips.location",
                    ),
                ),
                (
                    "passengers",
                    models.ManyToManyField(
                        related_name="trips",
                        through="trips.Seat",
                        to="orders.passenger",
                    ),
                ),
            ],
            options={
                "ordering": ["departure"],
                "verbose_name": "trip",
                "verbose_name_plural": "trips",
            },
        ),
        migrations.AddField(
            model_name="seat",
            name="trip",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="seats",
                to="trips.trip",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="seat",
            unique_together={("trip", "seat_number")},
        ),
        migrations.AlterField(
            model_name="seat",
            name="seat_number",
            field=models.PositiveIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(60),
                ],
                verbose_name="seat number",
            ),
        ),
        migrations.AlterField(
            model_name="seat",
            name="seat_status",
            field=models.CharField(
                choices=[
                    ("A", "Available"),
                    ("B", "Booked"),
                    ("R", "Reserved"),
                    ("H", "Onhold"),
                ],
                default="A",
                max_length=1,
                verbose_name="seat status",
            ),
        ),
        migrations.AlterField(
            model_name="seat",
            name="seat_type",
            field=models.CharField(
                choices=[
                    ("C", "Cama"),
                    ("S", "Semicama"),
                    ("E", "Executive"),
                    ("O", "Other"),
                ],
                default="C",
                max_length=1,
                verbose_name="seat type",
            ),
        ),
        migrations.CreateModel(
            name="Route",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="name")),
                ("slug", models.SlugField(max_length=200, verbose_name="slug")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to="routes/%Y/%m/%d", verbose_name="image"
                    ),
                ),
                (
                    "duration",
                    models.FloatField(
                        default=3.5,
                        validators=[
                            django.core.validators.MinValueValidator(0.1),
                            django.core.validators.MaxValueValidator(100),
                        ],
                        verbose_name="Duration in Hours",
                    ),
                ),
                ("price", models.JSONField(default=dict, verbose_name="price")),
                ("active", models.BooleanField(default=True, verbose_name="active")),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="routes",
                        to="companies.company",
                    ),
                ),
                (
                    "destination",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="routes_inbound",
                        to="trips.location",
                    ),
                ),
                (
                    "origin",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="routes_outbound",
                        to="trips.location",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("C", "Cama"),
                            ("S", "Semicama"),
                            ("E", "Executive"),
                            ("O", "Other"),
                        ],
                        default="S",
                        max_length=2,
                        verbose_name="category",
                    ),
                ),
            ],
            options={
                "verbose_name": "route",
                "verbose_name_plural": "routes",
            },
        ),
        migrations.CreateModel(
            name="Stop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("arrival", models.TimeField(verbose_name="arrival")),
                ("departure", models.TimeField(verbose_name="departure")),
                ("order", trips.fields.OrderField(blank=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="route_stops",
                        to="trips.location",
                    ),
                ),
                (
                    "route",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stops",
                        to="trips.route",
                    ),
                ),
            ],
            options={
                "verbose_name": "stop",
                "verbose_name_plural": "stops",
                "ordering": ("order",),
            },
        ),
        migrations.AlterModelOptions(
            name="seat",
            options={"verbose_name": "seat", "verbose_name_plural": "seats"},
        ),
    ]
