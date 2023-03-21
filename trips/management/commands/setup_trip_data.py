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

from companies.models import Company
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

    def success(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def danger(self, msg):
        self.stdout.write(self.style.HTTP_BAD_REQUEST(msg))

    def handle(self, *args, **kwargs):
        start = timer()

        locale = kwargs.get("locale")

        self.success("Locale: %s" % locale)
        self.danger("Deleting old data...")
        # TODO: Revisit this. could be dangerous if run in production.
        Company.objects.all().delete()
        Location.objects.all().delete()
        Trip.objects.all().delete()

        self.success("Creating new data...")

        with factory.Faker.override_default_locale(locale):
            make_trips()

        self.stdout.write(
            f"""
        Locations : {Location.objects.count()}
        Trips     : {Trip.objects.count()}
        Seats     : {Seat.objects.count()}
        """
        )
        end = timer()

        self.danger("took:%0.2f seconds..." % (end - start))
        self.success("All done! 💖💅🏻💫")
