# Generated by Django 4.1.5 on 2023-02-06 17:10

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
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
                ("name", models.CharField(max_length=50)),
                (
                    "email",
                    models.EmailField(
                        help_text="We'll email the ticket to this email id.",
                        max_length=254,
                    ),
                ),
                (
                    "residence",
                    django_countries.fields.CountryField(
                        help_text="This helps us to show you the best payment options.",
                        max_length=2,
                    ),
                ),
                ("paid", models.BooleanField(default=False)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_on"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
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
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "quantity",
                    models.PositiveSmallIntegerField(
                        default=1,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Passenger",
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
                    "document_type",
                    models.CharField(
                        choices=[
                            (None, "Identification"),
                            ("DNI", "DNI"),
                            ("PASSPORT", "PASSPORT"),
                            ("CE", "CEDULA"),
                            ("LE", "LE"),
                            ("LC", "LC"),
                            ("CUIT", "CUIT"),
                            ("NIE", "NIE"),
                            ("RG", "RG"),
                            ("RNE", "RNE"),
                            ("CPF", "CPF"),
                            ("RUT", "RUT"),
                            ("CURP", "CURP"),
                            ("CNPJ", "CNPJ"),
                        ],
                        max_length=10,
                    ),
                ),
                ("document_number", models.CharField(max_length=50)),
                ("nationality", django_countries.fields.CountryField(max_length=2)),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                (
                    "gender",
                    models.CharField(
                        choices=[(None, "Gender"), ("F", "Female"), ("M", "Male")],
                        max_length=1,
                    ),
                ),
                ("birth_date", models.DateField()),
                (
                    "phone_number",
                    models.CharField(
                        max_length=17,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                                regex="^\\+?1?\\d{9,15}$",
                            )
                        ],
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_on"],
            },
        ),
        migrations.AddIndex(
            model_name="passenger",
            index=models.Index(
                fields=["-created_on"], name="orders_pass_created_b7ac92_idx"
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="orders.order",
            ),
        ),
    ]
