import factory
from factory import fuzzy
from faker import Faker

from trips.factories import TripFactory

from .models import Order, OrderItem, Passenger

fake = Faker()


class OrderFactory(factory.django.DjangoModelFactory):
    """
    Factory to create fake orders in the system.
    """

    class Meta:
        model = Order

    name = factory.Faker("name_nonbinary")
    email = factory.LazyAttribute(
        lambda obj: "%s@example.com" % obj.name.replace(" ", "-").lower()
    )
    residence = factory.Faker("country_code")
    paid = factory.Faker("boolean")


class OrderItemFactory(factory.django.DjangoModelFactory):
    """
    Factory to create each order item.
    """

    class Meta:
        model = OrderItem
        django_get_or_create = ("order",)

    order = factory.SubFactory(OrderFactory)
    trip = factory.SubFactory(TripFactory)
    price = factory.LazyAttribute(lambda o: o.trip.price)
    quantity = factory.Faker("random_int", min=1, max=5)


class PassengerFactory(factory.django.DjangoModelFactory):
    """
    Factory to create dummy passengers travelling in our awesome buses. 💅🏻🚌🗺️
    """

    class Meta:
        model = Passenger

    order_item = factory.SubFactory(OrderItemFactory)
    document_type = fuzzy.FuzzyChoice(
        Passenger.DOCUMENT_TYPE_CHOICES[1:], getter=lambda c: c[0]
    )
    document_number = factory.Faker("ssn")
    nationality = factory.Faker("country_code")
    first_name = factory.Faker("first_name_nonbinary")
    last_name = factory.Faker("last_name_nonbinary")
    gender = factory.Faker("random_element", elements=["M", "F"])
    birth_date = factory.Faker("date_of_birth")
    phone_number = factory.LazyAttribute(
        lambda _: (fake.country_calling_code() + fake.phone_number())[:14]
    )
    seat_number = factory.Faker("random_int", min=1, max=60)
