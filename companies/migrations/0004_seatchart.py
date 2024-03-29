# Generated by Django 4.2.2 on 2023-07-12 17:16

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0003_company_owner"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeatChart",
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
                ("title", models.CharField(max_length=200)),
                ("json", models.JSONField()),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seatcharts",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ("title",),
            },
        ),
    ]
