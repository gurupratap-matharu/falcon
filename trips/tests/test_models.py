from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from companies.factories import CompanyFactory
from orders.factories import PassengerFactory
from orders.models import Passenger
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

    def test_location_slug_is_auto_generated_even_if_not_supplied(self):
        location = Location.objects.create(name="san carlos de bariloche")

        self.assertEqual(location.slug, "san-carlos-de-bariloche")

    def test_existing_slug_is_not_overwritten_when_updating_location(self):
        location = Location.objects.create(name="san carlos de bariloche")

        self.assertEqual(location.slug, "san-carlos-de-bariloche")

        obj, created = Location.objects.update_or_create(
            name="san carlos de bariloche", defaults={"name": "SAN CARLOS DE BARILOCHE"}
        )
        self.assertEqual(obj.slug, "san-carlos-de-bariloche")

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
        Location.objects.all().delete()
        _ = Location.objects.create(name="Mendoza", slug="mendoza")

        with self.assertRaises(IntegrityError):
            # repeat the same slug
            Location.objects.create(name="Mendoza Terminal", slug="mendoza")


class TripModelTests(TestCase):
    """Test suite for the Trip Model"""

    def setUp(self) -> None:
        self.trip = TripFactory()
        self.seats = SeatFactory.create_batch(size=5, trip=self.trip)

    def test_str_representation(self):
        self.assertEqual(str(self.trip), f"{self.trip.name}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.trip._meta.verbose_name_plural), "trips")

    def test_get_absolute_url(self):
        trip_from_db = Trip.objects.first()

        actual_url = trip_from_db.get_absolute_url()  # type:ignore
        expected_url = f"/trips/{trip_from_db.id}/{trip_from_db.slug}/"  # type:ignore

        self.assertEqual(actual_url, expected_url)

    def test_get_add_to_cart_url_is_correct(self):
        trip_from_db = Trip.objects.first()

        actual_url = trip_from_db.get_add_to_cart_url()  # type:ignore
        expected_url = f"/cart/add/{trip_from_db.id}/"  # type:ignore

        self.assertEqual(actual_url, expected_url)

    def test_trip_model_creation_is_accurate(self):
        trip_from_db = Trip.objects.first()

        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(trip_from_db.name, self.trip.name)
        self.assertEqual(trip_from_db.slug, self.trip.slug)
        self.assertEqual(trip_from_db.company, self.trip.company)
        self.assertEqual(trip_from_db.origin, self.trip.origin)
        self.assertEqual(trip_from_db.destination, self.trip.destination)
        self.assertEqual(trip_from_db.departure, self.trip.departure)
        self.assertEqual(trip_from_db.arrival, self.trip.arrival)
        self.assertEqual(trip_from_db.price, self.trip.price)
        self.assertEqual(trip_from_db.description, self.trip.description)
        self.assertEqual(trip_from_db.mode, self.trip.mode)
        self.assertEqual(trip_from_db.status, self.trip.status)
        self.assertEqual(trip_from_db.image, self.trip.image)

        self.assertEqual(trip_from_db.seats.count(), len(self.seats))

    def test_all_fields_max_length(self):
        trip = Trip.objects.first()

        self.assertEqual(trip._meta.get_field("name").max_length, 200)
        self.assertEqual(trip._meta.get_field("slug").max_length, 200)

    def test_slug_is_auto_generated_even_if_not_supplied(self):
        origin, destination = LocationFactory.create_batch(size=2)
        company = CompanyFactory()
        departure = datetime.now(tz=ZoneInfo("UTC"))
        arrival = departure + timedelta(hours=1)

        # create trip but do not pass slug
        trip = Trip.objects.create(
            name="san carlos de bariloche",
            company=company,
            origin=origin,
            destination=destination,
            departure=departure,
            arrival=arrival,
            price=10000,
        )

        expected = "san-carlos-de-bariloche"
        actual = trip.slug

        self.assertEqual(expected, actual)

        # Update the trip with valid slug. This should not update the slug itself
        # else it breaks our SEO
        new_name = "SAN CARLOS DE BARILOCHE"
        obj, created = Trip.objects.update_or_create(
            name="san carlos de bariloche", defaults={"name": new_name}
        )
        self.assertEqual(obj.slug, expected)
        self.assertEqual(obj.name, new_name)

    def test_for_trip_in_the_past_a_seat_cannot_be_booked(self):
        # Create a past trip with two seats
        SeatFactory.reset_sequence(1)
        past_trip = TripPastFactory()
        seat = SeatFactory.create(trip=past_trip, seat_status=Seat.AVAILABLE)

        with self.assertRaises(TripException):
            past_trip.book_seat(seat)  # type:ignore

    def test_for_trip_with_no_seats_available_seat_cannot_be_booked(self):
        SeatFactory.reset_sequence(1)
        trip = TripTomorrowFactory()
        seat = SeatFactory.create(trip=trip, seat_status=Seat.BOOKED)

        with self.assertRaises(Exception):
            trip.book_seat(seat)  # type:ignore

    def test_a_trip_can_only_book_its_own_seat_correctly(self):
        trip = TripTomorrowFactory()

        seat = SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

        trip.book_seat(seat)  # type:ignore

        self.assertEqual(seat.seat_status, Seat.BOOKED)

    def test_a_trip_cannot_book_another_trips_seat_even_if_its_available(self):
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
        next_hour = datetime.now(tz=ZoneInfo("UTC")) + timedelta(hours=1)
        trip = TripFactory(departure=next_hour)

        self.assertTrue(trip.is_due_shortly)  # type:ignore

    def test_trip_booked_seats_is_correctly_generated(self):
        # Create an upcoming trip with random seats
        trip = TripTomorrowFactory()
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.AVAILABLE)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.BOOKED)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.ONHOLD)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.RESERVED)

        # Make sure except available seats all are returned
        self.assertEqual(len(trip.get_booked_seats()), 6)

    def test_trip_active_manager_returns_only_future_trips(self):
        Trip.objects.all().delete()

        # Make an upcoming & a past trip with both having active status
        _ = TripTomorrowFactory(status=Trip.ACTIVE)
        _ = TripPastFactory(status=Trip.ACTIVE)

        # Make sure past trip is not returned in active manager
        self.assertEqual(len(Trip.future.all()), 1)

    def test_trip_can_mark_seats_for_hold_correctly(self):
        Trip.objects.all().delete()

        # Make a trip with two available seats
        trip = TripTomorrowFactory()
        seat_1, seat_2 = SeatFactory.create_batch(
            size=2, seat_status=Seat.AVAILABLE, trip=trip
        )

        # Make sure initially they are available
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)

        # Get list of seat numbers for our trip eg: [1, 2] and mark them for hold
        seat_numbers = f"{seat_1.seat_number}, {seat_2.seat_number}"
        trip.hold_seats(seat_numbers)  # type: ignore

        seat_1.refresh_from_db()
        seat_2.refresh_from_db()

        # Verify that their status is set to ONHOLD
        self.assertEqual(seat_1.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_2.seat_status, Seat.ONHOLD)

    def test_trip_arrival_date_cannot_be_before_departure_date(self):
        departure = timezone.now()
        arrival = timezone.now() - timedelta(days=1)

        trip = TripFactory(departure=departure, arrival=arrival)

        with self.assertRaises(ValidationError):
            trip.full_clean()  # type:ignore

    def test_trip_can_book_seats_with_passengers_correctly(self):
        Trip.objects.all().delete()

        trip = TripTomorrowFactory()
        seat_1, seat_2 = SeatFactory.create_batch(
            size=2, trip=trip, seat_status=Seat.AVAILABLE
        )
        _ = PassengerFactory.create_batch(size=2)
        passengers = Passenger.objects.all()
        seat_numbers = f"{seat_1.seat_number}, {seat_2.seat_number}"

        # Verify seats are available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)
        self.assertIsNone(seat_2.passenger)

        # Book the seats with passengers
        seat_1, seat_2 = trip.book_seats_with_passengers(seat_numbers, passengers)

        self.assertEqual(seat_1.seat_status, Seat.BOOKED)
        self.assertEqual(seat_2.seat_status, Seat.BOOKED)

        self.assertEqual(seat_1.passenger, passengers[0])
        self.assertEqual(seat_2.passenger, passengers[1])

    def test_trip_booking_seats_with_no_passengers_raises_valid_error(self):
        Trip.objects.all().delete()

        trip = TripTomorrowFactory()
        seat_1, seat_2 = SeatFactory.create_batch(
            size=2, trip=trip, seat_status=Seat.AVAILABLE
        )
        seat_numbers = f"{seat_1.seat_number}, {seat_2.seat_number}"

        # Verify seats are available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)
        self.assertIsNone(seat_2.passenger)

        # Book the seats with passengers
        with self.assertRaises(ValidationError):
            trip.book_seats_with_passengers(seat_numbers, None)

        # Verify seats are still available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)
        self.assertIsNone(seat_2.passenger)

    def test_trip_booking_seats_with_no_seats_raises_valid_error(self):
        Trip.objects.all().delete()

        trip = TripTomorrowFactory()
        seat_1, seat_2 = SeatFactory.create_batch(
            size=2, trip=trip, seat_status=Seat.AVAILABLE
        )

        _ = PassengerFactory.create_batch(size=2)
        passengers = Passenger.objects.all()

        seat_numbers = " "  # <-- pass empty seat string

        # Verify seats are available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)
        self.assertIsNone(seat_2.passenger)

        # Book the seats with passengers
        with self.assertRaises(ValidationError):
            trip.book_seats_with_passengers(seat_numbers, passengers)

        # Verify seats are still available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)
        self.assertIsNone(seat_2.passenger)

    def test_trip_booking_mismatched_passengers_and_seats_raises_valid_error(self):
        Trip.objects.all().delete()

        trip = TripTomorrowFactory()
        seat_1 = SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

        _ = PassengerFactory.create_batch(size=2)
        passengers = Passenger.objects.all()

        seat_numbers = (
            f"{seat_1.seat_number} "  # <-- pass only one seat for two passengers
        )

        # Verify seats are available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)

        # Book the seats with passengers
        with self.assertRaises(ValidationError):
            trip.book_seats_with_passengers(seat_numbers, passengers)

        # Verify seats are still available with no passengers assigned
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertIsNone(seat_1.passenger)


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
