"""A utility script to load fake trip data into the db for the trips app.

Running this script should create
    - Locations
    - Trips
    - Seats
with sensible defaults.
"""

from timeit import default_timer as timer

from django.core.management.base import BaseCommand

import factory

from trips.factories import make_trips, make_trips_for_company
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
        num_trips = kwargs.get("trips") or 20
        num_seats = kwargs.get("seats") or 40

        self.success("Locale: %s" % locale)
        self.success("Total Trips: %s" % num_trips)
        self.success("Seats Per Trip: %s" % num_seats)

        self.danger("Deleting old data...")
        # TODO: Revisit this. could be dangerous if run in production.
        Trip.objects.all().delete()

        self.success("Creating new data...")

        with factory.Faker.override_default_locale(locale):
            self.success("\nCreating trips...")
            make_trips(num_trips=int(num_trips), num_seats=int(num_seats))

        self.stdout.write(
            f"""
        Locations : {Location.objects.count()}
        Trips     : {Trip.objects.count()}
        Seats     : {Seat.objects.count()}
        """
        )
        end = timer()

        self.danger("took:%0.2f seconds..." % (end - start))
        self.success("All done!")
