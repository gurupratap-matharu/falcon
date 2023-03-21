import datetime
import logging
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, F, FloatField, IntegerField, Q
from django.db.models.functions import Cast, Round
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .exceptions import SeatException, TripException
from .seat_map import SEAT_MAP

logger = logging.getLogger(__name__)


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

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            logger.info("slugifying %s:%s..." % (self.name, slugify(self.name)))
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FutureManager(models.Manager):
    """
    Extra manager for Trip Model which shows only active trips

    A trip is active when
        - departure is in the future
        - status is set to Active
    """

    def get_queryset(self):
        logger.info("showing only future trips(⏰)...")

        qs = super().get_queryset()
        return qs.filter(departure__gt=timezone.now())

    def active(self):
        logger.info("showing only active trips(🌳)...")

        return self.filter(status=Trip.ACTIVE)

    def for_company(self, company_slug=None):
        """Build the Queryset with relevant stats for only one company"""

        logger.info("showing only trips for company(🚌):%s..." % company_slug)

        availability = Count("seats", filter=Q(seats__seat_status=Seat.AVAILABLE))
        occupied = Cast(
            Count("seats", filter=~Q(seats__seat_status=Seat.AVAILABLE)), FloatField()
        )
        total = Cast(Count("seats"), FloatField())

        # Convert occupancy to % of nearest multiple of 5 for progress bars
        occupancy = Cast(100 * occupied / total, IntegerField())
        occupancy = 5 * Round(occupancy / 5)
        
        # Find revenue = price * occupied seats
        revenue = Cast(F("price"), FloatField()) * occupied
        revenue = Cast(revenue, IntegerField())

        qs = self.filter(company__slug=company_slug)
        qs = qs.annotate(availability=availability)
        qs = qs.annotate(occupancy=occupancy)
        qs = qs.annotate(revenue=revenue)
        qs = qs.select_related("company", "origin", "destination")
        qs = qs.order_by("departure")

        return qs

    def __repr__(self):
        return "I only show trips from the future 🔮"


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
        to="companies.Company",
        on_delete=models.CASCADE,
        related_name="trips",
    )
    passengers = models.ManyToManyField(
        to="orders.Passenger", through="Seat", related_name="trips"
    )
    orders = models.ManyToManyField(
        to="orders.Order", through="orders.OrderItem", related_name="trips"
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
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1)]
    )
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

    objects = models.Manager()
    future = FutureManager()

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            logger.info("slugifying %s:%s..." % (self.name, slugify(self.name)))
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def clean(self):
        # Don't allow arrival date to be less than departure date
        if self.arrival and self.departure and (self.arrival < self.departure):
            raise ValidationError(
                {"arrival": _("Arrival date cannot be less than departure date")},
                code="invalid",
            )

    def __str__(self):
        """
        # TODO: Can be made better
        """
        return self.name

    # TODO implemente custom model manager to
    # Filter trips by - (origin, destination, date)
    # Should return only trips that are
    #   - due in the future
    #   - have seats available
    #   - having status active and not onhold or other
    #   - ordered by most booked to least booked

    def get_absolute_url(self):
        # TODO: Veer can we make this <origin>/<destination>/<company>/<id>?
        # Like how blog posts have unique urls
        return reverse_lazy(
            "trips:trip_detail", kwargs={"id": self.id, "slug": self.slug}
        )

    def get_add_to_cart_url(self):
        return reverse_lazy("cart:cart_add", kwargs={"trip_id": self.id})

    def get_update_url(self):
        return reverse_lazy(
            "companies:trip-update",
            kwargs={"slug": self.company.slug, "id": str(self.id)},
        )

    def get_passenger_list_url(self):
        return reverse_lazy(
            "companies:trip-detail",
            kwargs={"slug": self.company.slug, "id": str(self.id)},
        )

    def get_status_context(self):
        context = "success" if self.status == Trip.ACTIVE else "danger"
        return context

    def book_seat(self, seat):
        """Mark a seat as booked"""

        if not seat.trip == self:
            raise TripException("Seat %s does not belong to this trip!" % seat)
        elif not self.is_active:
            raise TripException("Trip %s is not active", self)
        else:
            seat.book()

    def hold_seats(self, seat_numbers: list[str] | list[int]):
        """Update seat status to hold"""

        if not seat_numbers:
            raise ValidationError("Seat numbers cannot be null 💣💥💣")

        seat_numbers = [s.strip() for s in seat_numbers.split(",")]
        return self.seats.filter(seat_number__in=seat_numbers).update(
            seat_status=Seat.ONHOLD
        )

    def book_seats_with_passengers(
        self, seat_numbers: list[str] | list[int], passengers
    ):
        """Update seat status to Booked and link a passenger to it"""

        if not seat_numbers.strip():
            raise ValidationError("seat numbers cannot be null 💺💥💺")

        if not passengers:
            raise ValidationError("passengers cannot be null ���💥💺�👭💺💥💺")

        seat_numbers = [s.strip() for s in seat_numbers.split(",")]
        seats = self.seats.filter(seat_number__in=seat_numbers)

        logger.info("checking these seats...%s", seats)

        # verify that seats count and passenger count match
        # this is suboptimal logic in my opinion.
        # TODO: improve this
        seats_count, passengers_count = seats.count(), passengers.count()
        if seats_count != passengers_count:
            raise ValidationError(
                "Seats count %(seats)s does not match passengers count %(passengers)s",
                code="invalid",
                params={"seats": seats_count, "passengers": passengers_count},
            )

        # TODO: revisit this to improve the query
        for s, p in zip(seats, passengers):
            logger.info("allotting 👩‍🦳 %s: 💺 %s..." % (p, s))
            s.seat_status = Seat.BOOKED
            s.passenger = p
            s.save()

        return seats

    def get_booked_seats(self):
        """
        Get list of booked seats for populating seatchart.js

        TODO: Rename this to Unavailable seats.
        Since a seat on hold | reserved is not booked but rather unavailable!
        """

        logger.info("calculating booked seats(🔖)...")
        return [
            s.get_row_col()
            for s in self.seats.all()  # type:ignore
            if s.seat_status != Seat.AVAILABLE
        ]

    @property
    def seats_available(self) -> int:
        """Calculate the number of seats available for a trip"""
        return sum(
            s.seat_status == Seat.AVAILABLE for s in self.seats.all()
        )  # type:ignore

    @property
    def duration(self):
        """Calculates the trip duration in hours"""
        td = self.arrival - self.departure
        return td.seconds // 3600

    @property
    def is_active(self) -> bool:
        """Is the trip due in the future"""
        return self.departure > timezone.now()

    @property
    def has_departed(self) -> bool:
        """Whether the trip has already departed"""
        return self.departure < timezone.now()

    @property
    def is_due_shortly(self) -> bool:
        """Whether the departure is due within a day"""
        return self.departure <= timezone.now() + datetime.timedelta(days=1)

    @property
    def is_running(self) -> bool:
        """Is the trip currently in transit"""
        return self.departure < timezone.now() < self.arrival


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
    ONHOLD = "H"
    SEAT_STATUS_CHOICES = [
        (AVAILABLE, "Available"),
        (BOOKED, "Booked"),
        (RESERVED, "Reserved"),
        (ONHOLD, "Onhold"),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="seats")
    passenger = models.ForeignKey(
        "orders.Passenger", on_delete=models.CASCADE, related_name="seats", null=True
    )
    seat_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    seat_type = models.CharField(choices=SEAT_TYPE_CHOICES, default=CAMA, max_length=1)
    seat_status = models.CharField(
        choices=SEAT_STATUS_CHOICES, default=AVAILABLE, max_length=1
    )

    def __str__(self):
        return f"{str(self.seat_number)}"

    def get_row_col(self):
        """Get a row col representation of a seat number"""

        return SEAT_MAP.get(str(self.seat_number))

    def book(self):
        """Mark a seat as booked only if its available."""

        if not self.seat_status == Seat.AVAILABLE:
            raise SeatException(
                "Seat %s has status %s and cannot be booked!"
                % (self.seat_number, self.get_seat_status_display())  # type:ignore
            )

        logger.info("booking seat: %s", self)
        self.seat_status = Seat.BOOKED
        self.save()
