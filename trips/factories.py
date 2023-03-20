import logging
import random
from datetime import datetime as dt
from datetime import timedelta as td
from zoneinfo import ZoneInfo

from django.template.defaultfilters import slugify

import factory
from factory import fuzzy
from faker import Faker

from companies.factories import CompanyFactory
from trips.models import Location, Seat, Trip
from trips.terminals import TERMINALS
from companies.samples import COMPANIES

fake = Faker()
logger = logging.getLogger(__name__)


class CustomImageField(factory.django.ImageField):
    def _make_data(self, params):
        color = params.pop("color", "blue")
        if callable(color):
            color = color()
        params["color"] = color
        return super(CustomImageField, self)._make_data(params)


class LocationFactory(factory.django.DjangoModelFactory):
    """Factory to create all bus terminals"""

    class Meta:
        model = Location
        django_get_or_create = ("slug",)

    name = factory.Faker("random_element", elements=TERMINALS)
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    abbr = factory.LazyAttribute(lambda o: o.name.lower()[:3])


class TripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trip

    company = factory.SubFactory(CompanyFactory)
    name = factory.LazyAttribute(lambda o: f"{o.origin} - {o.destination}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    origin = factory.SubFactory(LocationFactory)
    destination = factory.SubFactory(LocationFactory)
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
    image = CustomImageField(color=fake.color)


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
        end_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=2),
    )


class TripDayAfterTomorrowFactory(TripFactory):
    """Only create trips which are due to run day after tomorrow 😂"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=2),
        end_dt=dt.now(tz=ZoneInfo("UTC")) + td(days=3),
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
        lambda o: Seat.SEAT_TYPE_CHOICES[2][0]
        if o.seat_number < 7
        else Seat.SEAT_TYPE_CHOICES[1][0]
    )
    seat_status = fuzzy.FuzzyChoice(Seat.SEAT_STATUS_CHOICES, getter=lambda c: c[0])


class SeatWithPassengerFactory(SeatFactory):
    """
    Create a `Booked` seat with a passenger assigned to it 💁‍♀️
    """

    seat_status = Seat.BOOKED
    # We provide dotted path for passenger factory to avoid circular import error
    passenger = factory.SubFactory("orders.factories.PassengerFactory")


def make_trips():
    ORIGIN = "Buenos Aires"
    DESTINATION = "Mendoza"

    logger.info("creating all companies...")
    for name in COMPANIES:
        CompanyFactory(name=name)

    logger.info("creating all locations...")
    for name in TERMINALS:
        LocationFactory(name=name)

    # Create our favorite locations
    origin = LocationFactory(name=ORIGIN)
    destination = LocationFactory(name=DESTINATION)

    # Create trips
    logger.info("creating all trips...")

    trips_random = TripFactory.create_batch(size=10)
    trips_outbound = TripTomorrowFactory.create_batch(
        size=2, origin=origin, destination=destination
    )
    trips_return = TripDayAfterTomorrowFactory.create_batch(
        size=2, origin=destination, destination=origin
    )

    trips = trips_random + trips_outbound + trips_return

    # Create seats in each trip
    logger.info("creating all seats...")

    for trip in trips:
        SeatFactory.reset_sequence(1)

        # Create some booked seats with a passenger assigned to it
        SeatWithPassengerFactory.create_batch(size=20, trip=trip)

        # Create available empty seats
        SeatFactory.create_batch(size=20, trip=trip, seat_status=Seat.AVAILABLE)

    return trips


def make_trips_for_company(company=None):
    """
    This is an encompassing method that focusses on building random trips only for
    one company.

    This can be especially useful in dashboard visualizations.
    """

    # Create all the terminals
    for terminal in TERMINALS:
        LocationFactory(name=terminal)

    # Choose two random locations
    origin = LocationFactory()
    destination = LocationFactory()

    # Create trips
    trips_random = TripFactory.create_batch(size=10, company=company)

    # Create future active outbound trips
    trips_outbound = TripTomorrowFactory.create_batch(
        size=5,
        company=company,
        status=Trip.ACTIVE,
        origin=origin,
        destination=destination,
    )
    # Create future active return trips
    trips_return = TripDayAfterTomorrowFactory.create_batch(
        size=5,
        company=company,
        status=Trip.ACTIVE,
        origin=destination,
        destination=origin,
    )  # <-- Note how we have swapped origin and destination to create return trip

    trips = trips_random + trips_outbound + trips_return

    # Create seats in each trip
    for trip in trips:

        total_seats = 40
        booked_seats = random.randint(1, total_seats)  # nosec
        empty_seats = total_seats - booked_seats

        SeatFactory.reset_sequence(1)
        SeatWithPassengerFactory.create_batch(size=booked_seats, trip=trip)

        # Create available empty seats
        SeatFactory.create_batch(
            size=empty_seats, trip=trip, seat_status=Seat.AVAILABLE
        )

    return trips
    return trips
