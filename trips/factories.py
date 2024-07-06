import itertools
import logging
import random
from datetime import date
from datetime import datetime as dt
from datetime import timedelta as td
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify

import factory
from django_countries import countries
from factory import fuzzy
from faker import Faker

from companies.factories import CompanyFactory
from trips.models import Location, Route, Seat, Stop, Trip
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
    abbr = factory.LazyAttribute(lambda o: o.name.lower()[:5])

    address_line1 = factory.Faker("address")
    city = factory.Faker("city")
    state = factory.Faker("state")
    postal_code = factory.Faker("postalcode")
    country = factory.Faker("random_element", elements=list(dict(countries)))

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
    category = fuzzy.FuzzyChoice(Route.CATEGORY_CHOICES, getter=lambda c: c[0])
    duration = fuzzy.FuzzyFloat(1, 24, precision=2)
    price = factory.LazyAttribute(
        lambda o: {
            f"{o.origin.abbr.strip()};{o.destination.abbr.strip()}": fake.random_number(
                digits=5
            )
        }
    )


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

    route = factory.SubFactory(RouteFactory)
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
    price = fuzzy.FuzzyDecimal(low=5000, high=20000)
    status = fuzzy.FuzzyChoice(Trip.TRIP_STATUS_CHOICES, getter=lambda c: c[0])
    mode = fuzzy.FuzzyChoice(Trip.TRIP_MODE_CHOICES, getter=lambda c: c[0])
    description = factory.Faker("paragraph")


class TripPastFactory(TripFactory):
    """Only create trips which are already in the past"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=dt.now(tz=ZoneInfo("UTC")) - td(days=90),
        end_dt=dt.now(tz=ZoneInfo("UTC")) - td(days=5),
    )


class TripTomorrowFactory(TripFactory):
    """Only create trips which are due to run tomorrow"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=1),
        end_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=1),
    )


class TripDayAfterTomorrowFactory(TripFactory):
    """Only create trips which are due to run day after tomorrow 😂"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=2),
        end_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=2),
    )


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

    # Create trips
    logger.info("creating all trips...")
    for route in routes:
        logger.info("Route:%s" % route)
        trip = TripTomorrowFactory(route=route, status=Trip.ACTIVE)

    # Create seats in each trip
    logger.info("creating all seats...")

    size = num_seats // 2
    trips = Trip.objects.all()

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
