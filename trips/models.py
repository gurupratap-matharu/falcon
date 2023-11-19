import logging
import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from trips.exceptions import SeatException, TripException
from trips.managers import FutureManager, PastManager
from trips.seat_map import SEAT_MAP

logger = logging.getLogger(__name__)


class Location(models.Model):
    """
    Represents any location where a trip can start or stop. This include
    origin, destination and all intermediate stops.

    In domain sense this can be a bus terminal for intercity buses.
    """

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    abbr = models.CharField(
        verbose_name=_("abbreviation"),
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

    def get_absolute_url(self):
        return reverse_lazy("locations:location-detail", kwargs={"slug": self.slug})


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
    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200)
    origin = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="trips_outbound"
    )
    destination = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="trips_inbound"
    )
    departure = models.DateTimeField(verbose_name=_("Departure Date & Time"))
    arrival = models.DateTimeField(verbose_name=_("Arrival Date & Time"))
    price = models.DecimalField(
        _("price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        _("status"),
        max_length=2,
        choices=TRIP_STATUS_CHOICES,
        default=ACTIVE,
    )
    mode = models.CharField(
        _("mode"),
        max_length=2,
        choices=TRIP_MODE_CHOICES,
        default=DIRECT,
    )
    image = models.ImageField(_("image"), upload_to="trips/%Y/%m/%d", blank=True)
    description = models.TextField(_("description"), blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    future = FutureManager()
    past = PastManager()

    class Meta:
        ordering = ["departure"]

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
        return "success" if self.status == Trip.ACTIVE else "danger"

    def book_seat(self, seat):
        """Mark a seat as booked"""

        if not seat.trip == self:
            raise TripException("Seat %s does not belong to this trip!" % seat)
        elif not self.is_active:
            raise TripException("Trip %s is not active", self)
        else:
            seat.book()

    def hold_seats(self, seat_numbers: list[str] | list[int]):
        """Update seat status to ONHOLD"""
        # TODO: Change the argument seat_number from list to *args or *seat_numbers
        # We should not use lists as function arguments!

        if not seat_numbers:
            raise ValidationError("Seat numbers cannot be null 💣💥💣")

        seat_numbers = [s.strip() for s in seat_numbers.split(",")]

        logger.info("holding seats:%s..." % seat_numbers)

        return self.seats.filter(
            seat_status=Seat.AVAILABLE, seat_number__in=seat_numbers
        ).update(seat_status=Seat.ONHOLD)

    def release_seats(self, seat_numbers: list[str] | list[int]):
        """Update seat status to AVAILABLE"""
        # TODO: Change the argument seat_number from list to *args or *seat_numbers
        # We should not use lists as function arguments!

        if not seat_numbers:
            raise ValidationError("Seat numbers cannot be null 💣💥💣")

        seat_numbers = [s.strip() for s in seat_numbers.split(",")]

        logger.info("releasing seats:%s..." % seat_numbers)

        return self.seats.filter(
            seat_status=Seat.ONHOLD, seat_number__in=seat_numbers
        ).update(seat_status=Seat.AVAILABLE)

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
    def duration(self) -> str:
        """Calculates the trip duration in hours as string"""
        td = self.arrival - self.departure
        return ":".join(str(td).split(":")[:2])

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
        return self.departure <= timezone.now() + timedelta(days=1)

    @property
    def is_running(self) -> bool:
        """Is the trip currently in transit"""
        return self.departure < timezone.now() < self.arrival

    def create_seats(self, *seat_numbers):
        """
        Create multiple seats for a trips in one go based on a list of
        seat numbers.
        """

        logger.info("creating seats...")
        logger.info("seats: %s", (seat_numbers,))

        # TODO
        # Is try except needed here? Or an atomic transaction.

        objs = [
            Seat(trip=self, seat_number=seat_number) for seat_number in seat_numbers
        ]

        return Seat.objects.bulk_create(objs)

    def create_occurrences(self, departures):
        """
        Create multiple occurrences for a trip in one go based on a list
        of departure timestamps.
        """

        logger.info("trip: %s" % self)
        logger.info("departures: %s" % departures)
        logger.info("creating occurrences...")

        objs = []

        duration = self.arrival - self.departure

        for departure in departures:
            arrival = departure + duration
            obj = Trip(
                name=self.name,
                slug=self.slug,
                company=self.company,
                origin=self.origin,
                destination=self.destination,
                departure=departure,
                arrival=arrival,
                price=self.price,
                status=self.status,
                mode=self.mode,
                image=self.image,
                description=self.description,
            )
            objs.append(obj)

        return Trip.objects.bulk_create(objs)


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
        _("seat number"), validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    seat_type = models.CharField(
        _("seat type"), choices=SEAT_TYPE_CHOICES, default=CAMA, max_length=1
    )
    seat_status = models.CharField(
        _("seat status"), choices=SEAT_STATUS_CHOICES, default=AVAILABLE, max_length=1
    )

    class Meta:
        unique_together = ("trip", "seat_number")

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
