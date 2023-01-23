from django.db import models
from django.utils.translation import gettext_lazy as _


def company_cover_path(instance, filename):
    return f"companies/{instance.slug}/covers/{filename}"


def company_thumbnail_path(instance, filename):
    return f"companies/{instance.slug}/thumbnails/{filename}"


class Company(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.CharField(max_length=800, blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    cover = models.ImageField(
        verbose_name=_("Cover photo"), upload_to=company_cover_path, blank=True
    )
    thumbnail = models.ImageField(
        verbose_name=_("Thumbnail photo"), upload_to=company_thumbnail_path, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "company"
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name
