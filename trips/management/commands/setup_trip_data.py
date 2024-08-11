"""A utility script to load fake trip data into the db for the trips app.

Running this script should create
    - Locations
    - Trips
    - Seats
with sensible defaults.
"""

import logging
from timeit import default_timer as timer

from django.core.management.base import BaseCommand

import factory

from trips.factories import make_trips
from trips.models import Location, Seat, Trip

logger = logging.getLogger(__name__)


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
        num_trips = kwargs.get("trips") or 20
        num_seats = kwargs.get("seats") or 40

        logger.info("Locale: %s" % locale)
        logger.info("Total Trips: %s" % num_trips)
        logger.info("Seats Per Trip: %s" % num_seats)

        logger.info("Creating new data...")

        with factory.Faker.override_default_locale(locale):
            self.success("\nCreating trips...")
            make_trips(num_trips=int(num_trips), num_seats=int(num_seats))

        logger.info("Locations:%s" % Location.objects.count())
        logger.info("Trips:%s" % Trip.objects.count())
        logger.info("Seats:%s" % Seat.objects.count())

        end = timer()

        logger.info("took:%0.2f seconds..." % (end - start))
        self.success("All done!")
