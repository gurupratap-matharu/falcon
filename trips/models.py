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

    def book_seat(self, seat):
        """Mark a seat as booked"""

        if seat.trip == self:
            seat.book()
        else:
            raise Exception("Seat %s does not belong to this trip!" % seat)

    @property
    def seats_available(self) -> int:
        """Calculate the number of seats available for a trip"""
        return sum(s.seat_status == "A" for s in self.seats.all())

    @property
    def revenue(self):
        """Calculate the cost of all booked seats"""
        return sum(s.price for s in self.seats.all() if s.seat_status == Seat.BOOKED)

    @property
    def duration(self):
        """Calculates the trip duration in hours"""
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


class Seat(models.Model):
    CAMA = "C"
    SEMICAMA = "S"
    EXECUTIVE = "E"
    OTHER = "O"
    SEAT_TYPE_CHOICES = [
        (CAMA, "Cama"),
        (SEMICAMA, "Semicama"),
        (EXECUTIVE, "Executive"),
        (OTHER, "Other"),
    ]

    AVAILABLE = "A"
    BOOKED = "B"
    RESERVED = "R"
    SEAT_STATUS_CHOICES = [
        (AVAILABLE, "Available"),
        (BOOKED, "Booked"),
        (RESERVED, "Reserved"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    seat_type = models.CharField(choices=SEAT_TYPE_CHOICES, default=CAMA, max_length=1)
    seat_status = models.CharField(
        choices=SEAT_STATUS_CHOICES, default=AVAILABLE, max_length=1
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{str(self.seat_number)}"

    def book(self):
        """Mark a seat as booked only if its available."""

        if self.seat_status == Seat.AVAILABLE:
            self.seat_status = Seat.BOOKED
            self.save()
        else:
            raise Exception(
                "Seat %s has status %s and cannot be booked!"
                % (self.seat_number, self.get_seat_status_display())  # type:ignore
            )
