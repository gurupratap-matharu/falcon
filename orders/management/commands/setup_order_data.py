"""A utility script to load fake order data into the db for the orders app.

Running this script should create
    - Orders
    - OrderItems
    - Passengers
with sensible defaults.
"""


import random

from django.core.management.base import BaseCommand

import factory

from orders.factories import OrderFactory, OrderItemFactory, PassengerFactory
from orders.models import Order, OrderItem, Passenger


class Command(BaseCommand):
    """
    Management command which cleans and populates database with mock data
    """

    help = "Loads fake orders data into the database"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "-l",
            "--locale",
            type=str,
            help="Define a locale for the data to be generated.",
        )

    def handle(self, *args, **kwargs):
        locale = kwargs.get("locale")

        self.stdout.write(self.style.SUCCESS("Locale: %s" % locale))

        self.stdout.write(self.style.HTTP_BAD_REQUEST("Deleting old data..."))

        # TODO: Revisit this. could be dangerous if run in production.
        # Note deleting orders directly deletes all orderitems and passengers as well due to models.CASCADE.
        Order.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Creating new data..."))

        with factory.Faker.override_default_locale(locale):
            orders = OrderFactory.create_batch(size=10)

            for order in orders:
                
                num_trips = random.randint(1, 2)
                num_passengers = random.randint(1, 5)

                _ = OrderItemFactory.create_batch(
                    size=num_trips, order=order, quantity=num_passengers
                )
                _ = PassengerFactory.create_batch(size=num_passengers, order=order)

        self.stdout.write(
            f"""
        Orders: {Order.objects.count()}
        OrderItems: {OrderItem.objects.count()}
        Passengers: {Passenger.objects.count()}
        """
        )

        self.stdout.write(self.style.SUCCESS("All done! 💖💅🏻💫"))
