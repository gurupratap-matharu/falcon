# Generated by Django 4.1.3 on 2022-12-13 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_customuser_bio_customuser_location_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
