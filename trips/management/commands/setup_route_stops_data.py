from timeit import default_timer as timer

from django.core.management import call_command
from django.core.management.base import BaseCommand

from trips.models import Route


class Command(BaseCommand):
    """
    Simple command to populate the database with a list of route and stops.
    """

    help = "Creates a bunch of routes with stops in the database"

    def handle(self, *args, **kwargs):
        start = timer()

        call_command("loaddata", "routes.json.gz")
        end = timer()

        routes = Route.objects.count()

        self.stdout.write("took:%0.2f seconds." % (end - start))
        self.stdout.write(f"Total routes:{routes}")
        self.stdout.write("All done!")
