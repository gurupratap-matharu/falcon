import logging
import uuid
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField

from trips.exceptions import SeatException, TripException
from trips.fields import OrderField
from trips.managers import FutureManager, LocationManager, PastManager
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
        unique=True,
        help_text=_("Used internally as a reference"),
    )
    address_line1 = models.CharField(_("Address line 1"), max_length=128, blank=True)
    address_line2 = models.CharField(_("Address line 2"), max_length=128, blank=True)
    city = models.CharField(_("City"), max_length=64, blank=True)
    state = models.CharField(_("State/Province"), max_length=200, blank=True)
    postal_code = models.CharField(_("Postal Code"), max_length=10, blank=True)
    country = CountryField(blank_label=_("(select country)"))
    latitude = models.DecimalField(
        _("Latitude"), max_digits=9, decimal_places=6, null=True
    )
    longitude = models.DecimalField(
        _("Longitude"), max_digits=9, decimal_places=6, null=True
    )

    objects = LocationManager()

    class Meta:
        ordering = ["name"]
        verbose_name = _("location")
        verbose_name_plural = _("locations")

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.abbr,)

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse_lazy("locations:location-detail", kwargs={"slug": self.slug})


class Route(models.Model):
    """
    An operators creates routes which are blueprints of a line they operate on.
    They are abstract in nature and don't belong to any particular date as such but have
    all the information like stops, pricing, origin, destination, departure and arrivals.

    Trips are created based on routes and have a date on which they run.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        to="companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        related_name="routes",
    )
    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    image = models.ImageField(_("image"), upload_to="routes/%Y/%m/%d", blank=True)

    origin = models.ForeignKey(
        "trips.Location",
        on_delete=models.SET_NULL,
        null=True,
        related_name="routes_outbound",
    )
    destination = models.ForeignKey(
        "trips.Location",
        on_delete=models.SET_NULL,
        null=True,
        related_name="routes_inbound",
    )
    duration = models.FloatField(
        _("Duration in Hours"),
        default=3.5,
        validators=[MinValueValidator(0.1), MaxValueValidator(100)],
    )

    active = models.BooleanField(_("active"), default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("route")
        verbose_name_plural = _("routes")

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse_lazy(
            "companies:route-detail",
            kwargs={"id": str(self.id), "slug": self.company.slug},
        )

    def goes_from(self, origin, destination) -> bool:
        """
        Determine if this route goes from origin to destination.

        - Both origin and destination should be part of the route's stops
        - Origin should come before destination in the stop list i.e. origin's order
          should be less than destination's order.
        """
        try:
            qs = self.stops.all()
            origin_stop = qs.get(name=origin)
            destination_stop = qs.get(name=destination)

        except Stop.DoesNotExist:
            return False
        else:
            return origin_stop.order < destination_stop.order

    def get_schedule_for_date(self, departure_date) -> dict:
        """
        Builds a dict with departure datetimes for any arbitrary date for all the
        stops on the route.

        We use this as a json field on the trip model for fast querying.
        """

        stops = self.stops.select_related("name")
        start = stops.first().departure

        delta = departure_date - start.date()
        schedule = dict()

        # Build a dict with key as the location code
        for stop in stops:
            code = stop.name.abbr
            schedule[code] = {
                "order": stop.order,
                "arrival": stop.arrival + delta,
                "departure": stop.departure + delta,
            }

        return schedule

    def get_price(self, origin, destination, category):
        try:
            price = self.prices.get(
                origin=origin, destination=destination, category=category
            )
        except Price.DoesNotExist:
            logger.warning(
                "Price not set from %s to %s for category %s"
                % (origin, destination, category)
            )
            price = 0
        return price


class Stop(models.Model):
    """
    A route can have many intermediate stops in its journey. Each stop has an order in
    the route with an arrival & departure time.

    Eg route: A -> B -> C -> D

    Here we have four stops where orgin is A and destination is D. B & C would be intermediate
    stops.
    """

    name = models.ForeignKey(
        "trips.Location",
        on_delete=models.SET_NULL,
        null=True,
        related_name="route_stops",
    )
    route = models.ForeignKey(
        "trips.Route", on_delete=models.CASCADE, related_name="stops"
    )
    arrival = models.DateTimeField(
        _("arrival"), default=parse_datetime("2000-01-01T08:00:00-03:00")
    )
    departure = models.DateTimeField(
        _("departure"), default=parse_datetime("2000-01-01T08:00:00-03:00")
    )
    order = OrderField(for_fields=["route"], blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order",)
        verbose_name = _("stop")
        verbose_name_plural = _("stops")

    def __str__(self):
        return f"{self.order}. {self.name}"


class Price(models.Model):
    """
    The price for each stop combination on a route.
    """

    CAMA = "C"
    SEMICAMA = "S"
    EXECUTIVE = "E"
    OTHER = "O"
    CATEGORY_CHOICES = [
        (CAMA, "Cama"),
        (SEMICAMA, "Semicama"),
        (EXECUTIVE, "Executive"),
        (OTHER, "Other"),
    ]

    route = models.ForeignKey(
        "trips.Route", on_delete=models.CASCADE, related_name="prices"
    )
    origin = models.ForeignKey(
        "trips.Location", on_delete=models.CASCADE, related_name="+"
    )
    destination = models.ForeignKey(
        "trips.Location", on_delete=models.CASCADE, related_name="+"
    )
    amount = models.DecimalField(
        _("amount"), max_digits=10, decimal_places=2, validators=[MinValueValidator(1)]
    )
    category = models.CharField(
        _("category"), max_length=2, choices=CATEGORY_CHOICES, default=SEMICAMA
    )

    class Meta:
        ordering = ("route",)
        unique_together = ("route", "origin", "destination", "category")
        verbose_name = _("price")
        verbose_name_plural = _("prices")

    def __str__(self):
        return str(self.amount)

    def clean(self):
        # Don't allow price to be set for locations a route doesn't go to
        if not self.route.goes_from(self.origin, self.destination):
            raise ValidationError(
                "Route doesn't go from %(origin)s to %(destination)s",
                code="invalid",
                params={"origin": self.origin, "destination": self.destination},
            )


class Trip(models.Model):

    CAMA = "C"
    SEMICAMA = "S"
    EXECUTIVE = "E"
    OTHER = "O"
    CATEGORY_CHOICES = [
        (CAMA, "Cama"),
        (SEMICAMA, "Semicama"),
        (EXECUTIVE, "Executive"),
        (OTHER, "Other"),
    ]

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
    route = models.ForeignKey(
        to="trips.Route", on_delete=models.CASCADE, null=True, related_name="trips"
    )
    company = models.ForeignKey(
        to="companies.Company",
        on_delete=models.CASCADE,
        related_name="trips",
    )
    category = models.CharField(
        _("category"), max_length=2, choices=CATEGORY_CHOICES, default=SEMICAMA
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
        Location, on_delete=models.SET_NULL, null=True, related_name="trips_outbound"
    )
    destination = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, related_name="trips_inbound"
    )
    departure = models.DateTimeField(verbose_name=_("Departure Date & Time"))
    arrival = models.DateTimeField(verbose_name=_("Arrival Date & Time"))
    schedule = models.JSONField(_("schedule"), default=dict, encoder=DjangoJSONEncoder)
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
        verbose_name = _("trip")
        verbose_name_plural = _("trips")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            logger.debug("slugifying %s:%s..." % (self.name, slugify(self.name)))
            self.slug = slugify(self.name)

        return super().save(*args, **kwargs)

    def clean(self):
        # Don't allow arrival date to be less than departure date
        if self.arrival and self.departure and (self.arrival < self.departure):
            raise ValidationError(
                {"arrival": _("Arrival date cannot be less than departure date")},
                code="invalid",
            )

    def get_absolute_url(self):
        return reverse_lazy("trips:trip-detail", kwargs={"id": self.id})

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

    def hold_seats(self, seat_numbers: list[str | int]):
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

    def release_seats(self, seat_numbers: list[str | int]):
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

    def book_seats_with_passengers(self, seat_numbers: list[str | int], passengers):
        """
        TODO: Please refactor this method to be more precise and optimal.
        Update seat status to Booked and link a passenger to it
        """

        if not seat_numbers.strip() or not passengers:
            raise ValidationError("seat numbers or passengers cannot be null")

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

        for s, p in zip(seats, passengers):
            s.seat_status = Seat.BOOKED
            s.passenger = p
            s.save(update_fields=["seat_status", "passenger"])
            logger.info("allotted seat %s: to %s..." % (s, p))

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
        return self.route.duration

    def stops(self):
        return self.route.stops.select_related("name")

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
            schedule = self.route.get_schedule_for_date(departure.date())

            obj = Trip(
                route=self.route,
                name=self.name,
                slug=self.slug,
                company=self.company,
                description=self.description,
                origin=self.origin,
                destination=self.destination,
                departure=departure,
                arrival=arrival,
                status=self.status,
                mode=self.mode,
                schedule=schedule,
            )
            objs.append(obj)

        return Trip.objects.bulk_create(objs)

    def goes_from(self, origin, destination) -> bool:
        try:
            o = self.schedule[origin.abbr]
            d = self.schedule[destination.abbr]
        except KeyError:
            return False
        else:
            return o["order"] < d["order"]

    def get_schedule(self) -> dict:
        lst = sorted(self.schedule.items(), key=lambda x: x[1]["order"])
        return {k: v for k, v in lst}

    def get_duration(self, origin, destination) -> timedelta:
        if not self.goes_from(origin, destination):
            raise TripException(
                "Trip does not goes from %s to %s" % (origin, destination)
            )

        return self.get_arrival(destination) - self.get_departure(origin)

    def get_departure(self, location) -> datetime:
        try:
            ts = self.schedule[location.abbr]["departure"]
        except KeyError:
            raise TripException("Trip does not reach location:%s" % location)
        else:
            return parse_datetime(ts)

    def get_arrival(self, location) -> datetime:
        try:
            ts = self.schedule[location.abbr]["arrival"]
        except KeyError:
            raise TripException("Trip does not reach location:%s" % location)
        else:
            return parse_datetime(ts)

    def get_price(self, origin, destination):
        # TODO: Change to own price grid and not route's
        return self.route.get_price(origin, destination, self.category)


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
        "orders.Passenger", on_delete=models.SET_NULL, related_name="+", null=True
    )
    order_item = models.ForeignKey(
        "orders.OrderItem",
        null=True,
        on_delete=models.SET_NULL,
        related_name="booked_seats",
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
        verbose_name = _("seat")
        verbose_name_plural = _("seats")

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
        self.save(update_fields=["seat_status"])
