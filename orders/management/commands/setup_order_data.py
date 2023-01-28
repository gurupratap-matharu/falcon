"""A utility script to load fake order data into the db for the orders app.

Running this script should create
    - Orders
    - OrderItems
    - Passengers
with sensible defaults.
"""


from django.core.management.base import BaseCommand

import factory

from orders.factories import OrderItemFactory, PassengerFactory
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
            order_items = OrderItemFactory.create_batch(size=10)
            for order_item in order_items:
                _ = PassengerFactory.create_batch(size=2, order_item=order_item)

        self.stdout.write(
            f"""
        Orders: {Order.objects.count()}
        OrderItems: {OrderItem.objects.count()}
        Passengers: {Passenger.objects.count()}
        """
        )

        self.stdout.write(self.style.SUCCESS("All done! 💖💅🏻💫"))
