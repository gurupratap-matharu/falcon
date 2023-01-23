import datetime
import random
from zoneinfo import ZoneInfo

import factory
from django.template.defaultfilters import slugify
from factory import fuzzy
from faker import Faker

from companies.factories import CompanyFactory
from trips.models import Location, Trip
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
        lambda o: o.departure + datetime.timedelta(hours=random.randint(5, 48))
    )
    status = fuzzy.FuzzyChoice(Trip.TRIP_STATUS_CHOICES, getter=lambda c: c[0])
    mode = fuzzy.FuzzyChoice(Trip.TRIP_MODE_CHOICES, getter=lambda c: c[0])
    description = factory.Faker("paragraph")
    seats_available = factory.Faker("random_int", min=1, max=60)
    price = factory.Faker("random_int", min=2000, max=20000)
    image = CustomImageField(color=fake.color)
