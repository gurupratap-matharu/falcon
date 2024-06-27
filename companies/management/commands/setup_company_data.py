from timeit import default_timer as timer

from django.core.management.base import BaseCommand

from companies.factories import CompanyFactory
from companies.models import Company
from companies.samples import COMPANIES


class Command(BaseCommand):
    """
    Simple command to populate the database with a list of companies.
    """

    help = "Creates a bunch of companies in the database"

    def handle(self, *args, **kwargs):
        start = timer()
        for name in COMPANIES:
            c = CompanyFactory(name=name)
            self.stdout.write(f"created {c.name}")
        end = timer()
        total = Company.objects.count()

        self.stdout.write("took:%0.2f seconds." % (end - start))
        self.stdout.write(f"Total companies:{total}")
        self.stdout.write("All done!")
