import datetime
from zoneinfo import ZoneInfo

from django.db import IntegrityError
from django.test import TestCase

from trips.exceptions import SeatException, TripException
from trips.factories import (
    LocationFactory,
    SeatFactory,
    TripFactory,
    TripPastFactory,
    TripTomorrowFactory,
)
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
        # Create a past trip with two seats
        SeatFactory.reset_sequence(1)
        trip = TripPastFactory()
        seat = SeatFactory.create(trip=trip, seat_status=Seat.AVAILABLE)

        with self.assertRaises(TripException):
            trip.book_seat(seat)  # type:ignore

    def test_for_trip_with_no_seats_available_seat_cannot_be_booked(self):
        SeatFactory.reset_sequence(1)
        trip = TripTomorrowFactory()
        seat = SeatFactory.create(trip=trip, seat_status=Seat.BOOKED)

        with self.assertRaises(Exception):
            trip.book_seat(seat)  # type:ignore

    def test_a_trip_can_only_book_its_own_seat(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

        trip.book_seat(seat)  # type:ignore

        self.assertEqual(seat.seat_status, Seat.BOOKED)

    def test_a_trip_cannot_book_another_trips_seat(self):
        random_trip = TripTomorrowFactory()
        seat = SeatFactory(trip=self.trip, seat_status=Seat.AVAILABLE)

        with self.assertRaises(TripException):
            random_trip.book_seat(seat)  # type:ignore

        self.assertEqual(seat.seat_status, Seat.AVAILABLE)

    def test_a_trip_cannot_book_a_reserved_seat(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.RESERVED)

        with self.assertRaises(Exception):
            trip.book_seat(seat)  # type:ignore

        self.assertEqual(seat.seat_status, Seat.RESERVED)

    def test_a_trip_cannot_book_an_already_booked_seat(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.BOOKED)

        with self.assertRaises(Exception):
            trip.book_seat(seat)  # type:ignore

        self.assertEqual(seat.seat_status, Seat.BOOKED)

    def test_a_trip_can_book_a_valid_available_seat(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

        trip.book_seat(seat)  # type:ignore
        self.assertEqual(seat.seat_status, Seat.BOOKED)
        self.assertEqual(trip.seats_available, 0)  # type:ignore

    def test_trip_revenue_is_correctly_calculated(self):
        trip = TripTomorrowFactory(price=5)

        # Create two booked seats (counted in revenue)
        SeatFactory.create(trip=trip, seat_status=Seat.BOOKED)
        SeatFactory.create(trip=trip, seat_status=Seat.BOOKED)

        # Create an available seat (not counted in revenue)
        SeatFactory.create(trip=trip, seat_status=Seat.AVAILABLE)

        self.assertEqual(trip.revenue, 10)  # type:ignore

    def test_trip_seats_available_is_correctly_calculated(self):
        trip = TripTomorrowFactory()

        # Create all seats
        _ = SeatFactory.create_batch(size=3, trip=trip, seat_status=Seat.AVAILABLE)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.BOOKED)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.RESERVED)

        self.assertEqual(trip.seats_available, 3)  # type:ignore

    def test_trip_duration_is_correctly_in_hours(self):
        actual = self.trip.duration  # type:ignore

        time_delta = self.trip.arrival - self.trip.departure  # type:ignore
        expected = time_delta.seconds // 3600

        self.assertEqual(actual, expected)

    def test_trip_in_the_past_have_has_departed_status(self):
        trip = TripPastFactory()

        self.assertTrue(trip.departure)

    def test_trip_leaving_tomorrow_is_due_shortly(self):
        next_hour = datetime.datetime.now(tz=ZoneInfo("UTC")) + datetime.timedelta(
            hours=1
        )
        trip = TripFactory(departure=next_hour)

        self.assertTrue(trip.is_due_shortly)  # type:ignore


class SeatModelTests(TestCase):
    """Test suite for the Seat Model"""

    def setUp(self):
        SeatFactory.reset_sequence(1)

    def test_str_representation(self):
        seat = SeatFactory()

        self.assertEqual(str(seat), f"{seat.seat_number}")

    def test_verbose_name_plural(self):
        seat = SeatFactory()
        self.assertEqual(str(seat._meta.verbose_name_plural), "seats")  # type:ignore

    def test_seat_model_creation_is_accurate(self):
        trip = TripFactory()
        seat = SeatFactory(trip=trip)
        seat_from_db = Seat.objects.first()

        self.assertEqual(Seat.objects.count(), 1)
        self.assertEqual(seat_from_db.seat_number, seat.seat_number)
        self.assertEqual(seat_from_db.seat_type, seat.seat_type)
        self.assertEqual(seat_from_db.seat_status, seat.seat_status)
        self.assertEqual(seat_from_db.trip, seat.trip)

    def test_rebooking_a_booked_seat_raises_valid_exception(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.BOOKED)

        with self.assertRaises(SeatException):
            seat.book()  # type:ignore

    def test_booking_a_reserved_seat_raises_valid_exception(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.RESERVED)

        with self.assertRaises(SeatException):
            seat.book()  # type:ignore

    def test_booking_an_available_seat_works(self):
        trip = TripTomorrowFactory()
        seat = SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

        seat.book()  # type:ignore
        self.assertEqual(seat.seat_status, Seat.BOOKED)
        self.assertEqual(trip.revenue, trip.price)  # type:ignore
        self.assertEqual(trip.seats_available, 0)  # type:ignore