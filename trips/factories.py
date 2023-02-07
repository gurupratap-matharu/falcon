import datetime
import random
from zoneinfo import ZoneInfo

from django.template.defaultfilters import slugify

import factory
from factory import fuzzy
from faker import Faker

from companies.factories import CompanyFactory
from orders.factories import PassengerFactory
from trips.models import Location, Seat, Trip
from trips.terminals import TERMINALS

fake = Faker()


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
        start_dt=datetime.datetime.now(tz=ZoneInfo("UTC"))
        - datetime.timedelta(days=90),
        end_dt=datetime.datetime.now(tz=ZoneInfo("UTC")) + datetime.timedelta(days=90),
    )
    arrival = factory.LazyAttribute(
        lambda o: o.departure + datetime.timedelta(hours=random.randint(5, 48))  # nosec
    )
    price = fuzzy.FuzzyDecimal(low=5000, high=20000)
    status = fuzzy.FuzzyChoice(Trip.TRIP_STATUS_CHOICES, getter=lambda c: c[0])
    mode = fuzzy.FuzzyChoice(Trip.TRIP_MODE_CHOICES, getter=lambda c: c[0])
    description = factory.Faker("paragraph")
    image = CustomImageField(color=fake.color)


class TripPastFactory(TripFactory):
    """Only create trips which are already in the past"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=ZoneInfo("UTC"))
        - datetime.timedelta(days=90),
        end_dt=datetime.datetime.now(tz=ZoneInfo("UTC")) - datetime.timedelta(days=5),
    )


class TripTomorrowFactory(TripFactory):
    """Only create trips which are due to run tomorrow"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=ZoneInfo("UTC")) + datetime.timedelta(days=1),
        end_dt=datetime.datetime.now(tz=ZoneInfo("UTC")) + datetime.timedelta(days=2),
    )


class TripDayAfterTomorrowFactory(TripFactory):
    """Only create trips which are due to run day after tomorrow 😂"""

    departure = fuzzy.FuzzyDateTime(
        start_dt=datetime.datetime.now(tz=ZoneInfo("UTC")) + datetime.timedelta(days=2),
        end_dt=datetime.datetime.now(tz=ZoneInfo("UTC")) + datetime.timedelta(days=3),
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
    passenger = factory.SubFactory(PassengerFactory)


def make_trips():
    for terminal in TERMINALS:
        LocationFactory(name=terminal)

    # Create our favorite locations
    buenos_aires = LocationFactory(name="Buenos Aires")
    mendoza = LocationFactory(name="Mendoza")

    # Create trips
    trips_random = TripFactory.create_batch(size=10)
    trips_outbound = TripTomorrowFactory.create_batch(
        size=2, origin=buenos_aires, destination=mendoza
    )
    trips_return = TripDayAfterTomorrowFactory.create_batch(
        size=2, origin=mendoza, destination=buenos_aires
    )

    trips = trips_random + trips_outbound + trips_return

    # Create seats in each trip
    for trip in trips:
        SeatFactory.reset_sequence(1)

        # Create some booked seats with a passenger assigned to it
        _ = SeatWithPassengerFactory.create_batch(size=5, trip=trip)

        # Create random empty seats
        _ = SeatFactory.create_batch(size=35, trip=trip)

    return trips
