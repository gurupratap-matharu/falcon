"""A utility script to load fake trip data into the db for the trips app.

Running this script should create
    - Locations
    - Trips
    - Seats
with sensible defaults.
"""

from timeit import default_timer as timer

from django.core.management.base import BaseCommand
from django.utils import timezone

import factory

from trips.factories import make_trips
from trips.models import Location, Seat, Trip


class Command(BaseCommand):
    """
    Management command which cleans and populates database with mock data
    """

    help = "Loads fake trips data into the database"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "-l",
            "--locale",
            type=str,
            help="Define a locale for the data to be generated.",
        )
        parser.add_argument(
            "-t",
            "--trips",
            type=int,
            help="Total number of trips to be generated.",
        )
        parser.add_argument(
            "-s",
            "--seats",
            type=int,
            help="Total number of seats per trip.",
        )

    def success(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def danger(self, msg):
        self.stdout.write(self.style.HTTP_BAD_REQUEST(msg))

    def handle(self, *args, **kwargs):
        start = timer()

        locale = kwargs.get("locale")

        self.stdout.write("Locale: %s" % locale)
        self.stdout.write("Creating new data...")

        with factory.Faker.override_default_locale(locale):
            self.success("\nCreating trips...")
            make_trips()

        self.stdout.write("Locations:%s" % Location.objects.count())
        self.stdout.write("Trips:%s" % Trip.objects.count())
        self.stdout.write("Seats:%s" % Seat.objects.count())

        end = timer()
        ts = timezone.now().strftime("%c")

        self.stdout.write("took:%0.2f seconds..." % (end - start))
        self.success("[%s] All done!\n\n" % (ts))
