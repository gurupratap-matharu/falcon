# Generated by Django 5.0.3 on 2024-07-19 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trips", "0016_stop_arrival_stop_departure"),
    ]

    operations = [
        migrations.AlterField(
            model_name="location",
            name="abbr",
            field=models.CharField(
                blank=True,
                help_text="Used internally as a reference",
                max_length=7,
                unique=True,
                verbose_name="abbreviation",
            ),
        ),
    ]
