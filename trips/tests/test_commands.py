from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from trips.models import Location, Seat, Trip


class SetupTripDataTests(TestCase):
    def test_command_output(self):

        # Arrange
        self.assertFalse(Trip.objects.exists())

        # Act
        out = StringIO()
        call_command("setup_trip_data", stdout=out)

        # Assert: objects in DB
        self.assertTrue(Location.objects.exists())
        self.assertTrue(Trip.objects.exists())
        self.assertTrue(Seat.objects.exists())

        # Assert: command output
        self.assertIn("All done!", out.getvalue())
