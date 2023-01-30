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


class TripModelTests(TestCase):
    """Test suite for the Trip Model"""

    def setUp(self) -> None:
        self.trip = TripFactory()

    def test_str_representation(self):
        self.assertEqual(str(self.trip), f"{self.trip.name}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.trip._meta.verbose_name_plural), "trips")

    def test_trip_model_creation_is_accurate(self):
        trip_from_db = Trip.objects.first()

        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(trip_from_db.name, self.trip.name)
        self.assertEqual(trip_from_db.company, self.trip.company)
        self.assertEqual(trip_from_db.origin, self.trip.origin)
        self.assertEqual(trip_from_db.destination, self.trip.destination)
        self.assertEqual(trip_from_db.departure, self.trip.departure)

    def test_all_fields_max_length(self):
        trip = Trip.objects.first()

        self.assertEqual(trip._meta.get_field("name").max_length, 200)
        self.assertEqual(trip._meta.get_field("slug").max_length, 200)

    def test_for_trip_in_the_past_a_seat_cannot_be_booked(self):
        self.fail()

    def test_for_trip_with_no_seats_available_seat_cannot_be_booked(self):
        self.fail()

    def test_a_trip_can_only_book_its_own_seat(self):
        self.fail()

    def test_a_trip_cannot_book_another_trips_seat(self):
        self.fail()

    def test_a_trip_cannot_book_a_reserved_seat(self):
        self.fail()

    def test_a_trip_cannot_book_an_already_booked_seat(self):
        self.fail()

    def test_a_trip_can_book_a_valid_available_seat(self):
        self.fail()

    def test_trip_revenue_is_correctly_calculated(self):
        self.fail()

    def test_trip_seats_available_is_correctly_calculated(self):
        self.fail()

    def test_trip_duration_is_correctly_in_hours(self):
        self.fail()

    def test_trip_in_the_past_have_has_departed_status(self):
        self.fail()

    def test_trip_leaving_tomorrow_is_due_shortly(self):
        self.fail()


class SeatModelTests(TestCase):
    """Test suite for the Seat Model"""

    def setUp(self):
        pass
    def test_str_representation(self):
        self.fail()
    def test_verbose_name_plural(self):
        self.fail()
    def test_seat_model_creation_is_accurate(self):
        self.fail()

    def test_seat_number_min_max_values(self):
        self.fail()

    def test_rebooking_a_booked_seat_raises_valid_exception(self):
        self.fail()
    def test_booking_a_reserved_seat_raises_valid_exception(self):
        self.fail()

    def test_booking_an_available_seat_works(self):
        self.fail()