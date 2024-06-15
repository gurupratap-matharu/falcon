from django.template.defaultfilters import slugify

import factory
from factory import fuzzy
from faker import Faker

from .models import Company, SeatChart
from .samples import COMPANIES, SEAT_CHART_DICTS, SEAT_CHART_TITLES

fake = Faker()


class CustomImageField(factory.django.ImageField):
    def _make_data(self, params):
        return fake.image()


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company
        django_get_or_create = ("slug",)

    name = factory.Faker("random_element", elements=COMPANIES)
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.Faker("paragraph", nb_sentences=5)
    website = factory.LazyAttribute(lambda o: "%s.com.ar" % slugify(o.name))
    address = factory.Faker("address", locale="es_CL")
    phone = factory.Faker("phone_number", locale="es_CL")
    email = factory.LazyAttribute(lambda o: "comercial@%s.com.ar" % slugify(o.name))
    cover = CustomImageField(filename="logo.jpg")
    owner = factory.SubFactory("users.factories.CompanyOwnerFactory")


class SeatChartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SeatChart

    title = factory.Faker("random_element", elements=SEAT_CHART_TITLES)
    company = factory.SubFactory("companies.factories.CompanyFactory")
    json = fuzzy.FuzzyChoice(SEAT_CHART_DICTS)
