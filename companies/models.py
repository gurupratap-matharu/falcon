import logging

from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


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

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "company"
        verbose_name_plural = "companies"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            logger.info("slugifying %s:%s..." % (self.name, slugify(self.name)))
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy("companies:company_detail", kwargs={"slug": self.slug})

    def get_admin_url(self):
        return reverse_lazy("companies:dashboard", kwargs={"slug": self.slug})

    def get_trip_list_url(self):
        return reverse_lazy("companies:trip-list", kwargs={"slug": self.slug})

    def get_coupon_list_url(self):
        return reverse_lazy("companies:coupon-list", kwargs={"slug": self.slug})

    def get_coupon_create_url(self):
        return reverse_lazy("companies:coupon-create", kwargs={"slug": self.slug})

    def get_booking_url(self):
        return reverse_lazy("companies:company-book", kwargs={"slug": self.slug})
