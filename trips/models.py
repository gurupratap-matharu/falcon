import datetime
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from companies.models import Company


class Location(models.Model):
    """
    Represents any location where a trip can start or stop. This include
    origin, destination and all intermediate stops.

    In domain sense this can be a bus terminal for intercity buses.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    abbr = models.CharField(
        verbose_name=_("Abbreviation"),
        max_length=7,
        blank=True,
        help_text=_("Used internally as a reference"),
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Trip(models.Model):
    ACTIVE = "A"
    CANCELLED = "C"
    ONHOLD = "H"
    DELAYED = "D"
    OTHER = "O"
    TRIP_STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (CANCELLED, "Cancelled"),
        (ONHOLD, "OnHold"),
        (DELAYED, "Delayed"),
        (OTHER, "Other"),
    ]

    DIRECT = "D"
    INDIRECT = "I"
    OTHER = "O"
    TRIP_MODE_CHOICES = [
        (DIRECT, "Direct"),
        (INDIRECT, "Indirect"),
        (OTHER, "Other"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="trips",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    origin = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="trips_outbound"
    )
    destination = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="trips_inbound"
    )
    departure = models.DateTimeField(verbose_name=_("Departure Date & Time"))
    arrival = models.DateTimeField(verbose_name=_("Arrival Date & Time"))

    status = models.CharField(
        max_length=2,
        choices=TRIP_STATUS_CHOICES,
        default=ACTIVE,
    )
    mode = models.CharField(
        max_length=2,
        choices=TRIP_MODE_CHOICES,
        default=DIRECT,
    )
    image = models.ImageField(upload_to="trips/%Y/%m/%d", blank=True)
    description = models.TextField(blank=True)
    # Seat types not added yet
    seats_available = models.PositiveSmallIntegerField(
        default=45, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        # TODO: Can be made better
        """
        return self.name

    def get_absolute_url(self):
        return reverse("trips:trip_detail", kwargs={"id": self.id, "slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("cart:cart_add", kwargs={"trip_id": self.id})

    @property
    def duration(self):
        """Calculates the duration in hours"""

        td = self.arrival - self.departure
        return td.seconds // 3600

    @property
    def active(self) -> bool:
        """Is the trip due in the future"""
        return self.departure > timezone.now()

    @property
    def has_departed(self) -> bool:
        """Whether the trip has already departed"""
        return self.departure < timezone.now()

    @property
    def is_due(self) -> bool:
        """Whether the departure is due within a day"""
        return self.departure <= timezone.now() + datetime.timedelta(days=1)
