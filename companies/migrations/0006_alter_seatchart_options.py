# Generated by Django 5.0.3 on 2024-06-15 16:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0005_alter_company_address_alter_company_description_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="seatchart",
            options={
                "ordering": ("title",),
                "verbose_name": "seat chart",
                "verbose_name_plural": "seat charts",
            },
        ),
    ]
