from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone

from companies.factories import CompanyFactory
from orders.factories import PassengerFactory
from orders.models import Passenger
from trips.exceptions import SeatException, TripException
from trips.factories import (
    LocationFactory,
    RouteFactory,
    SeatFactory,
    StopFactory,
    TripFactory,
    TripPastFactory,
    TripTomorrowFactory,
)
from trips.models import Location, Route, Seat, Stop, Trip


class LocationModelTests(TestCase):
    """Test suite for the Location Model"""

    def setUp(self) -> None:
        self.location = LocationFactory()

    def test_str_representation(self):
        self.assertEqual(str(self.location), f"{self.location.name}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.location._meta.verbose_name), "location")
        self.assertEqual(str(self.location._meta.verbose_name_plural), "locations")

    def test_get_absolute_url(self):
        location_from_db = Location.objects.first()

        actual_url = location_from_db.get_absolute_url()
        expected_url = f"/locations/{location_from_db.slug}/"

        self.assertEqual(actual_url, expected_url)

    def test_location_model_creation_is_accurate(self):
        obj = Location.objects.first()

        self.assertEqual(Location.objects.count(), 1)

        self.assertEqual(obj.name, self.location.name)
        self.assertEqual(obj.slug, self.location.slug)
        self.assertEqual(obj.abbr, self.location.abbr)

        self.assertEqual(obj.address_line1, self.location.address_line1)
        self.assertEqual(obj.city, self.location.city)
        self.assertEqual(obj.state, self.location.state)
        self.assertEqual(obj.postal_code, self.location.postal_code)
        self.assertEqual(obj.country, self.location.country)

        self.assertEqual(obj.latitude, self.location.latitude)
        self.assertEqual(obj.longitude, self.location.longitude)

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

    def test_max_length_of_all_fields(self):
        location = Location.objects.first()

        def get_length(field_name):
            return location._meta.get_field(field_name).max_length

        self.assertEqual(get_length("name"), 200)
        self.assertEqual(get_length("slug"), 200)
        self.assertEqual(get_length("abbr"), 7)
        self.assertEqual(get_length("address_line1"), 128)
        self.assertEqual(get_length("address_line2"), 128)
        self.assertEqual(get_length("city"), 64)
        self.assertEqual(get_length("state"), 40)
        self.assertEqual(get_length("postal_code"), 10)

    def test_latitude_longitude_structure(self):
        location = Location.objects.first()

        self.assertEqual(location._meta.get_field("latitude").max_digits, 9)
        self.assertEqual(location._meta.get_field("longitude").max_digits, 9)

        self.assertEqual(location._meta.get_field("latitude").decimal_places, 6)
        self.assertEqual(location._meta.get_field("longitude").decimal_places, 6)

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


class RouteModelTests(TestCase):
    """Test suite for the Route Model"""

    def setUp(self):
        self.route = RouteFactory()

    def test_str_representation(self):
        self.assertEqual(str(self.route), f"{self.route.name}")

    def test_verbose_names(self):
        self.assertEqual(self.route._meta.verbose_name, "route")
        self.assertEqual(self.route._meta.verbose_name_plural, "routes")

    def test_get_absolute_url(self):
        self.skipTest("not yet implemented")

    def test_admin_url(self):
        actual = self.route.get_admin_url()
        expected = reverse_lazy(
            "companies:route-detail",
            kwargs={"slug": self.route.company.slug, "id": str(self.route.id)},
        )
        self.assertEqual(actual, expected)

    def test_route_model_creation_is_accurate(self):
        obj = Route.objects.first()

        self.assertEqual(Route.objects.count(), 1)

        self.assertEqual(obj.name, self.route.name)
        self.assertEqual(obj.slug, self.route.slug)
        self.assertEqual(obj.company, self.route.company)
        self.assertEqual(obj.description, self.route.description)
        self.assertEqual(obj.image, self.route.image)
        self.assertEqual(obj.category, self.route.category)
        self.assertEqual(obj.origin, self.route.origin)
        self.assertEqual(obj.destination, self.route.destination)
        self.assertEqual(obj.duration, self.route.duration)
        self.assertEqual(obj.price, self.route.price)
        self.assertEqual(obj.active, self.route.active)

    def test_route_slug_is_auto_generated_even_if_not_supplied(self):
        route = Route.objects.create(name="bariloche to mendoza")

        self.assertEqual(route.slug, "bariloche-to-mendoza")

    def test_existing_slug_is_not_overwritten_when_updating_route(self):
        name = "bariloche to mendoza"
        slug = "bariloche-to-mendoza"

        route = Route.objects.create(name=name)

        self.assertEqual(route.slug, slug)

        obj, created = Route.objects.update_or_create(
            name=name, defaults={"name": "BARILOCHE TO MENDOZA"}
        )
        self.assertEqual(obj.slug, slug)

    def test_max_length_of_all_fields(self):
        def get_length(field_name):
            return route._meta.get_field(field_name).max_length

        route = Route.objects.first()

        self.assertEqual(get_length("name"), 200)
        self.assertEqual(get_length("slug"), 200)

    def test_negative_duration_raises_error(self):
        with self.assertRaises(ValidationError):
            r = RouteFactory(duration=-1)
            # Django validators are run only on calling full_clean() method
            r.full_clean()

    def test_excess_duration_raises_error(self):
        with self.assertRaises(ValidationError):
            r = RouteFactory(duration=101)
            r.full_clean()

    def test_route_price_field(self):
        self.skipTest("Yet to implement")

    def test_route_goes_from_method_works_correctly(self):
        # make route go from a -> b -> c
        a, b, c = StopFactory.create_batch(size=3, route=self.route)

        # make some random stops not on route
        d, e = StopFactory.create_batch(size=2)

        loc_a, loc_b, loc_c = a.name, b.name, c.name
        loc_d, loc_e = d.name, e.name

        # Assert

        # route goes from a -> b, a -> c, b -> c
        self.assertTrue(self.route.goes_from(loc_a, loc_b))
        self.assertTrue(self.route.goes_from(loc_a, loc_c))
        self.assertTrue(self.route.goes_from(loc_b, loc_c))

        # route doesn't go from c -> b, c -> a, b -> a
        self.assertFalse(self.route.goes_from(loc_c, loc_b))
        self.assertFalse(self.route.goes_from(loc_c, loc_a))
        self.assertFalse(self.route.goes_from(loc_b, loc_a))

        # route doesn't go to random stops not part of route
        self.assertFalse(self.route.goes_from(loc_a, loc_d))
        self.assertFalse(self.route.goes_from(loc_a, loc_e))
        self.assertFalse(self.route.goes_from(loc_d, loc_b))
        self.assertFalse(self.route.goes_from(loc_d, loc_c))
        self.assertFalse(self.route.goes_from(loc_d, loc_e))


class StopModelTests(TestCase):
    """Test suite for the Stop Model"""

    def setUp(self):
        self.route = RouteFactory()
        self.stop = StopFactory(route=self.route)

    def test_str_representation(self):
        self.assertEqual(str(self.stop), f"{self.stop.order}. {self.stop.name}")

    def test_verbose_names(self):
        self.assertEqual(self.stop._meta.verbose_name, "stop")
        self.assertEqual(self.stop._meta.verbose_name_plural, "stops")

    def test_stops_are_ordered_as_per_their_order_field(self):
        stop_1, stop_2 = StopFactory.create_batch(size=2, route=self.route)

        # remember self.stop has order 0 and is already created in setUp()
        # query from db
        stop_db_0, stop_db_1, stop_db_2 = Stop.objects.all()

        self.assertEqual(self.stop._meta.ordering, ("order",))
        self.assertEqual(stop_db_0, self.stop)
        self.assertEqual(stop_db_1, stop_1)
        self.assertEqual(stop_db_2, stop_2)

    def test_get_absolute_url(self):
        self.skipTest("not yet implemented")

    def test_stop_model_creation_is_accurate(self):
        obj = Stop.objects.first()

        self.assertEqual(Stop.objects.count(), 1)

        self.assertEqual(obj.name, self.stop.name)
        self.assertEqual(obj.route, self.stop.route)
        self.assertEqual(obj.order, self.stop.order)
        self.assertEqual(obj.arrival, self.stop.arrival)
        self.assertEqual(obj.departure, self.stop.departure)

    def test_new_stops_have_order_automatically_created(self):
        stop_1, stop_2 = StopFactory.create_batch(size=2, route=self.route)

        self.assertEqual(self.stop.order, 0)
        self.assertEqual(stop_1.order, 1)
        self.assertEqual(stop_2.order, 2)


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

    def test_trip_seats_available_is_correctly_calculated(self):
        trip = TripTomorrowFactory()

        # Create all seats
        _ = SeatFactory.create_batch(size=3, trip=trip, seat_status=Seat.AVAILABLE)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.BOOKED)
        _ = SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.RESERVED)

        self.assertEqual(trip.seats_available, 3)  # type:ignore

    def test_trip_duration_is_correctly_calculated_in_hours_and_minutes(self):
        actual = self.trip.duration  # type:ignore

        td = self.trip.arrival - self.trip.departure  # type:ignore
        expected = ":".join(str(td).split(":")[:2])

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

    def test_trip_cannot_hold_seats_that_are_not_available(self):
        """
        A trip should not be able to put any seat that is not Available on hold
        i.e. Seats that are - Reserved, Booked, Other cannot be put on hold
        Only Available seats can be put on hold.
        """

        Trip.objects.all().delete()

        # Make a trip with two available seats
        trip = TripTomorrowFactory()
        seat_1 = SeatFactory(seat_status=Seat.BOOKED, trip=trip)
        seat_2 = SeatFactory(seat_status=Seat.RESERVED, trip=trip)

        # Make sure initially they are not available
        self.assertEqual(seat_1.seat_status, Seat.BOOKED)
        self.assertEqual(seat_2.seat_status, Seat.RESERVED)

        # Get list of seat numbers for our trip eg: [1, 2] and mark them for hold
        seat_numbers = f"{seat_1.seat_number}, {seat_2.seat_number}"
        trip.hold_seats(seat_numbers)  # type: ignore

        seat_1.refresh_from_db()
        seat_2.refresh_from_db()

        # Verify that their status is UNCHANGED
        self.assertEqual(seat_1.seat_status, Seat.BOOKED)
        self.assertEqual(seat_2.seat_status, Seat.RESERVED)

    def test_trip_can_release_seats_that_are_onhold(self):
        Trip.objects.all().delete()

        trip = TripTomorrowFactory()
        seat_1 = SeatFactory(seat_status=Seat.ONHOLD, trip=trip)
        seat_2 = SeatFactory(seat_status=Seat.ONHOLD, trip=trip)

        # Make sure initially they are on hold
        self.assertEqual(seat_1.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_2.seat_status, Seat.ONHOLD)

        # Get list of seat numbers for our trip eg: [1, 2] and mark them for hold
        seat_numbers = f"{seat_1.seat_number}, {seat_2.seat_number}"
        trip.release_seats(seat_numbers)  # type: ignore

        seat_1.refresh_from_db()
        seat_2.refresh_from_db()

        # Verify that their status is Available
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)

    def test_trip_cannot_release_seats_that_are_not_onhold(self):
        """
        A trip should not be able to put any seat that is not on hold to avaiable
        i.e. Seats that are - Reserved, Booked, Other cannot be made available
        Only Onhold seats can be made available.
        """

        Trip.objects.all().delete()

        # Make a trip with two available seats
        trip = TripTomorrowFactory()
        seat_1 = SeatFactory(seat_status=Seat.BOOKED, trip=trip)
        seat_2 = SeatFactory(seat_status=Seat.RESERVED, trip=trip)

        # Make sure initially they are not available
        self.assertEqual(seat_1.seat_status, Seat.BOOKED)
        self.assertEqual(seat_2.seat_status, Seat.RESERVED)

        # Get list of seat numbers for our trip eg: [1, 2] and mark them for hold
        seat_numbers = f"{seat_1.seat_number}, {seat_2.seat_number}"
        trip.release_seats(seat_numbers)  # type: ignore

        seat_1.refresh_from_db()
        seat_2.refresh_from_db()

        # Verify that their status is UNCHANGED
        self.assertEqual(seat_1.seat_status, Seat.BOOKED)
        self.assertEqual(seat_2.seat_status, Seat.RESERVED)

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

    def test_trip_create_occurrences_works_correctly(self):
        """Verify if bulk creation of future trips works as expected."""

        # Initially only one trip
        self.assertEqual(Trip.objects.count(), 1)

        # Create daily departures for the next 5 days
        now = timezone.now()
        departures = [now + timedelta(days=days) for days in range(1, 6)]

        trips = self.trip.create_occurrences(departures=departures)

        future_trip = trips[0]

        # Five trips should have been created
        self.assertEqual(len(trips), 5)
        # In DB total 6 trips
        self.assertEqual(Trip.objects.count(), 6)

        # Take random future trip. all fields should match
        self.assertEqual(future_trip.name, self.trip.name)
        self.assertEqual(future_trip.slug, self.trip.slug)
        self.assertEqual(future_trip.company, self.trip.company)
        self.assertEqual(future_trip.origin, self.trip.origin)
        self.assertEqual(future_trip.destination, self.trip.destination)
        self.assertEqual(future_trip.duration, self.trip.duration)
        self.assertEqual(future_trip.price, self.trip.price)
        self.assertEqual(future_trip.description, self.trip.description)
        self.assertEqual(future_trip.mode, self.trip.mode)
        self.assertEqual(future_trip.status, self.trip.status)
        self.assertEqual(future_trip.image, self.trip.image)

    def test_trip_create_seats_works_correctly(self):
        """Check if bulk creating seats works perfectly"""

        trip = self.trip
        # Let's remove all seats
        trip.seats.all().delete()

        # Check our trip has no seats
        self.assertEqual(trip.seats.count(), 0)

        # Let's create odd numbered seats: [1,3,5,7,9]
        seat_numbers = [x for x in range(1, 10) if x % 2]
        trip.create_seats(*seat_numbers)

        # Validate seats are correctly generated
        self.assertEqual(trip.seats.count(), 5)

        seat_numbers_in_db = trip.seats.values_list("seat_number", flat=True)
        self.assertEqual(seat_numbers, list(seat_numbers_in_db))


class SeatModelTests(TestCase):
    """Test suite for the Seat Model"""

    def setUp(self):
        SeatFactory.reset_sequence(1)

    def test_str_representation(self):
        seat = SeatFactory()

        self.assertEqual(str(seat), f"{seat.seat_number}")

    def test_verbose_name_plural(self):
        seat = SeatFactory()
        self.assertEqual(str(seat._meta.verbose_name_plural), "seats")

    def test_unique_together_constraint_is_present(self):
        seat = SeatFactory()
        self.assertEqual(seat._meta.unique_together[0], ("trip", "seat_number"))

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
        self.assertEqual(trip.seats_available, 0)  # type:ignore

    def test_creating_another_seat_with_same_seat_number_raises_integrity_error(self):
        """
        Each trip can only have unique seat numbers. Duplicates are not allowed.
        """

        # Create a trip with seat number 5
        trip = TripTomorrowFactory()
        s = SeatFactory(seat_number=5, trip=trip)

        # Make sure its correct
        self.assertEqual(s.seat_number, 5)

        # Try creating another seat with same number for the same trip
        # This should not be allowed
        try:
            with transaction.atomic():
                SeatFactory(seat_number=5, trip=trip)
                self.fail("Duplicate seat numbers created!")
        except IntegrityError:
            pass

        # Try creating seat with number 5 for another random trip
        # This is allowed.
        trip_2 = TripTomorrowFactory()
        s_2 = SeatFactory(seat_number=5, trip=trip_2)

        self.assertEqual(s_2.seat_number, 5)
        self.assertEqual(s_2.trip, trip_2)
