import logging
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class CompanyManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


def company_cover_path(instance, filename):
    return f"companies/{instance.slug}/covers/{filename}"


def company_thumbnail_path(instance, filename):
    return f"companies/{instance.slug}/thumbnails/{filename}"


class Company(models.Model):
    name = models.CharField(_("name"), max_length=200, unique=True)
    slug = models.SlugField(_("slug"), max_length=300, unique=True)
    description = models.CharField(_("description"), max_length=800, blank=True)
    website = models.URLField(_("website"), blank=True)
    address = models.CharField(_("address"), max_length=200)
    phone = models.CharField(_("phone"), max_length=20)
    email = models.EmailField(_("email"))
    cover = models.ImageField(
        verbose_name=_("Cover photo"),
        upload_to=company_cover_path,
        blank=True,
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

    objects = CompanyManager()

    class Meta:
        ordering = ["name"]
        verbose_name = _("company")
        verbose_name_plural = _("companies")

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            logger.info("slugifying %s:%s..." % (self.name, slugify(self.name)))
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def get_absolute_url(self):
        return reverse_lazy("companies:company_detail", kwargs={"slug": self.slug})

    def get_admin_url(self):
        return reverse_lazy("companies:dashboard", kwargs={"slug": self.slug})

    def get_route_list_url(self):
        return reverse_lazy("companies:route-list", kwargs={"slug": self.slug})

    def get_trip_list_url(self):
        return reverse_lazy("companies:trip-list", kwargs={"slug": self.slug})

    def get_coupon_list_url(self):
        return reverse_lazy("companies:coupon-list", kwargs={"slug": self.slug})

    def get_coupon_create_url(self):
        return reverse_lazy("companies:coupon-create", kwargs={"slug": self.slug})

    def get_booking_url(self):
        return reverse_lazy("companies:company-book", kwargs={"slug": self.slug})

    def get_seatchart_url(self):
        return reverse_lazy("companies:seatchart-list", kwargs={"slug": self.slug})

    def get_live_status_url(self):
        return reverse_lazy("companies:live-status", kwargs={"slug": self.slug})


class SeatChart(models.Model):
    """
    Represents a seat map to be used in UI for a specific seating requirement
    by a company.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("title"), max_length=200)
    json = models.JSONField(_("json"))
    company = models.ForeignKey(
        "Company", related_name="seatcharts", on_delete=models.CASCADE
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)
        verbose_name = _("seat chart")
        verbose_name_plural = _("seat charts")

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse_lazy(
            "companies:seatchart-detail",
            kwargs={"slug": self.company.slug, "id": self.id},
        )
