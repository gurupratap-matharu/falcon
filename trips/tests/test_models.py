from django.db import IntegrityError
from django.test import TestCase

from trips.factories import LocationFactory, SeatFactory, TripFactory
from trips.models import Location, Seat, Trip


class LocationModelTests(TestCase):
    """Test suite for the Location Model"""

    def setUp(self) -> None:
        self.location = LocationFactory()

    def test_str_representation(self):
        self.assertEqual(str(self.location), f"{self.location.name}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.location._meta.verbose_name_plural), "locations")

    def test_location_model_creation_is_accurate(self):
        location_from_db = Location.objects.first()

        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(location_from_db.name, self.location.name)
        self.assertEqual(location_from_db.slug, self.location.slug)
        self.assertEqual(location_from_db.abbr, self.location.abbr)

    def test_location_name_max_length(self):
        location = Location.objects.first()
        max_length = location._meta.get_field("name").max_length  # type:ignore

        self.assertEqual(max_length, 200)

    def test_location_slug_max_length(self):

        location = Location.objects.first()
        max_length = location._meta.get_field("slug").max_length  # type:ignore

        self.assertEqual(max_length, 200)

    def test_location_abbr_max_length(self):

        location = Location.objects.first()
        max_length = location._meta.get_field("abbr").max_length  # type:ignore

        self.assertEqual(max_length, 7)

    def test_locations_are_ordered_by_name(self):
        Location.objects.all().delete()

        l_1 = LocationFactory(name="Gama")
        l_2 = LocationFactory(name="Alpha")
        l_3 = LocationFactory(name="Beta")

        locations = Location.objects.all()

        self.assertEqual(locations[0], l_2)
        self.assertEqual(locations[1], l_3)
        self.assertEqual(locations[2], l_1)

        location = locations[0]
        ordering = location._meta.ordering[0]  # type: ignore

        self.assertEqual(ordering, "name")

    def test_all_locations_have_unique_slugs(self):
        _ = Location.objects.create(name="Mendoza", slug="mendoza")

        with self.assertRaises(IntegrityError):
            # repeat the same slug
            Location.objects.create(name="Mendoza Terminal", slug="mendoza")
