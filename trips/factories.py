import itertools
import logging
import random
import string
from datetime import datetime as dt
from datetime import timedelta as td
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.crypto import get_random_string

import factory
from factory import fuzzy
from faker import Faker

from companies.factories import CompanyFactory
from trips.models import Location, Price, Route, Seat, Stop, Trip
from trips.terminals import TERMINALS

fake = Faker()


logger = logging.getLogger(__name__)


class CustomImageField(factory.django.ImageField):
    def _make_data(self, params):
        return fake.image()


class LocationFactory(factory.django.DjangoModelFactory):
    """Factory to create all bus terminals"""

    class Meta:
        model = Location
        django_get_or_create = ("slug",)

    name = factory.Faker("random_element", elements=TERMINALS)
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    abbr = factory.LazyAttribute(
        lambda o: o.name.replace(" ", "").lower()[:4]
        + get_random_string(length=3, allowed_chars=string.digits)
    )

    address_line1 = factory.Faker("address")
    city = factory.Faker("city")
    state = factory.Faker("state")
    postal_code = factory.Faker("postalcode")
    country = "AR"

    latitude = factory.LazyAttribute(lambda _: round(fake.latitude(), 6))
    longitude = factory.LazyAttribute(lambda _: round(fake.longitude(), 6))


class RouteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Route

    company = factory.SubFactory(CompanyFactory)
    name = factory.LazyAttribute(lambda o: f"{o.origin} - {o.destination}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.LazyAttribute(
        lambda o: f"Trip from {o.origin} - {o.destination}.\n{fake.paragraph()}"
    )
    image = CustomImageField(filename="route.jpg")
    origin = factory.SubFactory(LocationFactory)
    destination = factory.SubFactory(LocationFactory)
    duration = fuzzy.FuzzyFloat(1, 24, precision=2)


class RouteWithStopsFactory(RouteFactory):
    @factory.post_generation
    def stops(self, create, extracted, **kwargs):
        if not create:
            # Simple build, or nothing to add, do nothing.
            return

        # Create stops for this route and add them
        StopFactory(route=self, name=self.origin)
        StopFactory.create_batch(size=2, route=self)
        StopFactory(route=self, name=self.destination)


class PriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Price

    route = factory.SubFactory(RouteWithStopsFactory)
    origin = factory.SubFactory(LocationFactory)
    destination = factory.SubFactory(LocationFactory)
    amount = fuzzy.FuzzyDecimal(low=10000, high=80000)
    category = fuzzy.FuzzyChoice(Price.CATEGORY_CHOICES, getter=lambda c: c[0])


class StopFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stop

    name = factory.SubFactory(LocationFactory)
    route = factory.SubFactory(RouteFactory)
    arrival = fuzzy.FuzzyDateTime(start_dt=dt(2008, 1, 1, tzinfo=ZoneInfo("UTC")))
    departure = factory.LazyAttribute(lambda o: o.arrival + td(minutes=10))


class TripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trip

    route = factory.SubFactory(RouteWithStopsFactory)
    company = factory.SelfAttribute("route.company")
    name = factory.LazyAttribute(lambda o: f"{o.origin} - {o.destination}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    origin = factory.SelfAttribute("route.origin")
    destination = factory.SelfAttribute("route.destination")
    departure = fuzzy.FuzzyDateTime(
        start_dt=dt.now(tz=ZoneInfo("UTC")) - td(days=90),
        end_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=90),
    )
    arrival = factory.LazyAttribute(
        lambda o: o.departure + td(hours=random.randint(5, 48))  # nosec
    )
    category = fuzzy.FuzzyChoice(Trip.CATEGORY_CHOICES, getter=lambda c: c[0])
    status = fuzzy.FuzzyChoice(Trip.TRIP_STATUS_CHOICES, getter=lambda c: c[0])
    mode = fuzzy.FuzzyChoice(Trip.TRIP_MODE_CHOICES, getter=lambda c: c[0])
    description = factory.Faker("paragraph")
    schedule = factory.lazy_attribute(
        lambda o: o.route.get_schedule_for_date(o.departure.date())
    )


class TripPastFactory(TripFactory):
    """Only create trips which are already in the past"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=dt.now(tz=ZoneInfo("UTC")) - td(days=90),
        end_dt=dt.now(tz=ZoneInfo("UTC")) - td(days=5),
    )


class TripTomorrowFactory(TripFactory):
    """Only create trips which are due to run tomorrow"""

    class Meta:
        exclude = ("build_departure",)

    def build_departure(obj):
        tomorrow = timezone.now() + td(days=1)
        depart_time = obj.route.stops.first().departure.time()
        departure = dt.combine(tomorrow, depart_time)
        return timezone.make_aware(departure)

    departure = factory.LazyAttribute(build_departure)


class TripDayAfterTomorrowFactory(TripFactory):
    """Only create trips which are due to run day after tomorrow 😂"""

    class Meta:
        exclude = ("build_departure",)

    def build_departure(obj):
        tomorrow = timezone.now() + td(days=2)
        depart_time = obj.route.stops.first().departure.time()
        departure = dt.combine(tomorrow, depart_time)
        return timezone.make_aware(departure)

    departure = factory.LazyAttribute(build_departure)


class SeatFactory(factory.django.DjangoModelFactory):
    """
    Factory to create seats for a trip.
    """

    class Meta:
        model = Seat

    trip = factory.SubFactory(TripFactory)
    seat_number = factory.Sequence(lambda n: int(n))
    seat_type = factory.LazyAttribute(
        lambda o: (
            Seat.SEAT_TYPE_CHOICES[2][0]
            if o.seat_number < 7
            else Seat.SEAT_TYPE_CHOICES[1][0]
        )
    )
    seat_status = fuzzy.FuzzyChoice(Seat.SEAT_STATUS_CHOICES, getter=lambda c: c[0])


class SeatWithPassengerFactory(SeatFactory):
    """
    Create a `Booked` seat with a passenger assigned to it 💁‍♀️
    """

    seat_status = Seat.BOOKED
    # We provide dotted path for passenger factory to avoid circular import error
    passenger = factory.SubFactory("orders.factories.PassengerFactory")


def make_trips(num_trips=20, num_seats=40):
    """
    Helper method to create trips for all routes
    """

    # Create locations
    logger.info("creating all locations...")

    for name in TERMINALS:
        LocationFactory(name=name)

    routes = Route.objects.all()
    if not routes:
        raise ValidationError("Please load all routes first")

    cama = Trip.CAMA
    semicama = Trip.SEMICAMA

    # Create trips
    for route in routes:

        logger.info("creating trips for route:%s" % route)

        trip_1 = TripTomorrowFactory(route=route, status=Trip.ACTIVE, category=semicama)
        trip_2 = TripTomorrowFactory(route=route, status=Trip.ACTIVE, category=cama)

        trip_3 = TripDayAfterTomorrowFactory(
            route=route, status=Trip.ACTIVE, category=semicama
        )
        trip_4 = TripDayAfterTomorrowFactory(
            route=route, status=Trip.ACTIVE, category=cama
        )

    trips = [trip_1, trip_2, trip_3, trip_4]

    # Create seats in each trip
    logger.info("creating all seats...")

    size = num_seats // 2

    for trip in trips:
        SeatFactory.reset_sequence(1)

        # Create some booked seats with a passenger assigned to it
        SeatWithPassengerFactory.create_batch(size=size, trip=trip)

        # Create available empty seats
        SeatFactory.create_batch(size=size, trip=trip, seat_status=Seat.AVAILABLE)

    return trips


def make_route_stops(num_routes=1, stops_per_route=7, company=None):
    """
    Make a route and add a couple of stops to it in one go.
    """

    size = stops_per_route - 2

    if company:
        company = CompanyFactory(name=company)
        routes = RouteFactory.create_batch(size=num_routes, company=company)
    else:
        routes = RouteFactory.create_batch(size=num_routes)

    for route in routes:
        # TODO: Add stop arrivals which should consecutive
        StopFactory(route=route, name=route.origin)  # Origin stop
        StopFactory.create_batch(size=size, route=route)  # Intermediate stops
        StopFactory(route=route, name=route.destination)  # Last stop

        # Generate price json
        qs = route.stops.select_related("name")
        combinations = itertools.combinations(qs, 2)
        price = dict()

        for a, b in combinations:
            code = f"{a.name.abbr.strip()};{b.name.abbr.strip()}"
            cost = fake.random_number(digits=5)
            price[code] = cost

        logger.info("price:%s" % price)
        route.price = price
        route.save(update_fields=["price"])
        logger.info("created route:%s" % route)

    return routes
