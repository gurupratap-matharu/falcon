import json

from django.template.defaultfilters import slugify

import factory
from faker import Faker

from .models import Company, SeatChart
from .samples import COMPANIES, SEAT_CHARTS

fake = Faker()


class CustomImageField(factory.django.ImageField):
    def _make_data(self, params):
        color = params.pop("color", "blue")
        if callable(color):
            color = color()
        params["color"] = color
        return super(CustomImageField, self)._make_data(params)


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company
        django_get_or_create = ("name",)

    name = factory.Faker("random_element", elements=COMPANIES)
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.Faker("paragraph", nb_sentences=5)
    website = factory.LazyAttribute(lambda o: "%s.com.ar" % slugify(o.name))
    address = factory.Faker("address", locale="es_CL")
    phone = factory.Faker("phone_number", locale="es_CL")
    email = factory.LazyAttribute(lambda o: "comercial@%s.com.ar" % slugify(o.name))
    cover = CustomImageField(color=fake.safe_color_name)
    owner = factory.SubFactory("users.factories.CompanyOwnerFactory")


class JSONFactory(factory.DictFactory):
    """
    Use with factory.Dict to make JSON strings.
    """

    @classmethod
    def _generate(cls, create, attrs):
        obj = super()._generate(create, attrs)
        return json.dumps(obj)


class SeatChartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SeatChart

    title = factory.Faker("random_element", elements=SEAT_CHARTS)
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    company = factory.SubFactory("companies.factories.CompanyFactory")
    json = factory.Dict({"badger": ["stoat"]}, dict_factory=JSONFactory)
