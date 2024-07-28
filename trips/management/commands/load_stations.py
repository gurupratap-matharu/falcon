import csv
import logging

from django.core.management.base import BaseCommand

from trips.models import Location

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Load stations.csv to the database"""

    def handle(self, **options):

        stations = self.read_stations()

        for city, station, address, lat_lon, url in stations:
            lat, lon = lat_lon.split(",")
            country = "AR"

            Location.objects.get_or_create(
                name=station,
                city=city,
                address_line1=address,
                latitude=lat,
                longitude=lon,
                country=country,
            )

        self.stdout.write("All Done 💄✨💫")

    def read_stations(self):
        with open("stations.csv", newline="") as csv_file:
            station_reader = csv.reader(csv_file, delimiter=" ", quotechar="|")
            stations = [tuple(row) for row in station_reader if row]

        return stations
