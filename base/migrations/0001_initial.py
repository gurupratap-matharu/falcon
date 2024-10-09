# Generated by Django 5.0.3 on 2024-10-09 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Settings",
            fields=[
                (
                    "name",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                (
                    "char_val",
                    models.CharField(
                        blank=True, default=None, max_length=100, null=True
                    ),
                ),
                ("int_val", models.IntegerField(blank=True, default=None, null=True)),
                ("bool_val", models.BooleanField(blank=True, default=None, null=True)),
                (
                    "dec_val",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=None,
                        max_digits=11,
                        null=True,
                    ),
                ),
                (
                    "date_time_val",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
            ],
            options={
                "verbose_name": "settings",
                "ordering": ["name"],
            },
        ),
    ]
