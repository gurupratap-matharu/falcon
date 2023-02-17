import random

import factory
from factory import fuzzy
from faker import Faker

from .models import Order, OrderItem, Passenger

fake = Faker()


class OrderFactory(factory.django.DjangoModelFactory):
    """
    Factory to create fake orders in the system.
    """

    class Meta:
        model = Order

    name = factory.Faker("name_nonbinary")
    # email = factory.LazyAttribute(
    #     lambda obj: "%s@example.com" % obj.name.replace(" ", "-").lower()
    # )
    email = "veerplaying@gmail.com"
    residence = factory.Faker("country_code")
    paid = factory.Faker("boolean")

    @factory.post_generation
    def passengers(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of passengers were passed in, use them
            for passenger in extracted:
                self.passengers.add(passenger)


class OrderItemFactory(factory.django.DjangoModelFactory):
    """
    Factory to create each order item.
    """

    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    # We provide dotted path to another factory to avoid circular import error
    trip = factory.SubFactory("trips.factories.TripFactory")
    price = factory.Iterator([10, 15, 20])
    quantity = factory.Faker("random_int", min=1, max=5)


class PassengerFactory(factory.django.DjangoModelFactory):
    """
    Factory to create dummy passengers travelling in our awesome buses. 💅🏻🚌🗺️
    """

    class Meta:
        model = Passenger

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


def make_order_data(size=20, trip=None):
    """
    Builds orders, orderitems, passengers for a particular trip or random trips.
    Used in the setup_order_data management command.

    Can be called standalone method to build order only for one trip.
    Encompasses all factories in this script.
    """

    # 1. Create random orders
    orders = OrderFactory.create_batch(size=size)

    for order in orders:

        # Each order can have only forward trip (1) or both forward and return trip (2)
        # Each order can have between 1-5 passengers
        num_trips = random.randint(1, 2)  # nosec
        num_passengers = random.randint(1, 5)  # nosec

        # 2. Create random passengers for each order
        passengers = PassengerFactory.create_batch(size=num_passengers)
        order.passengers.add(*passengers)
        order.save()

        # 3. If trip is given build all order items for this trip else use random trips
        if trip:
            OrderItemFactory.create_batch(
                size=num_trips,
                order=order,
                quantity=num_passengers,
                trip=trip,
                price=trip.price,
            )
        else:
            OrderItemFactory.create_batch(
                size=num_trips, order=order, quantity=num_passengers
            )

    return orders


def order_dict():
    return factory.build(dict, FACTORY_CLASS=OrderFactory)


def order_item_dict():
    return factory.build(dict, FACTORY_CLASS=OrderItemFactory)


def passenger_dict():
    return factory.build(dict, FACTORY_CLASS=PassengerFactory)
