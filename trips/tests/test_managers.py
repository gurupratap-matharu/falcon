from datetime import date, timedelta

from django.http import Http404
from django.test import TestCase
from django.utils import timezone

from companies.factories import CompanyFactory
from trips.factories import (
    LocationFactory,
    SeatFactory,
    TripDayAfterTomorrowFactory,
    TripPastFactory,
    TripTomorrowFactory,
)
from trips.models import Seat, Trip


class FutureManagerTests(TestCase):
    """
    Test suite for check all methods of future manager of trip model

        - get_queryset()
        - active()
        - search()
        - for_company()

    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.company_a = CompanyFactory()
        cls.company_b = CompanyFactory()

        cls.price = 10

        # Create two active trips in the future
        cls.future_active_trips_company_a = TripTomorrowFactory.create_batch(
            size=2, company=cls.company_a, status=Trip.ACTIVE, price=cls.price
        )

        # Create two active trips in the future for company B
        cls.future_active_trips_company_b = TripTomorrowFactory.create_batch(
            size=2, company=cls.company_b, status=Trip.ACTIVE, price=cls.price
        )
        # Create two cancelled trips in the future
        cls.future_inactive_trips = TripTomorrowFactory.create_batch(
            size=2, company=cls.company_a, status=Trip.CANCELLED, price=cls.price
        )

        cls.future_trips = (
            cls.future_active_trips_company_b
            + cls.future_active_trips_company_a
            + cls.future_inactive_trips
        )

        # Create two past trips
        cls.past_trips = TripPastFactory.create_batch(
            size=2, company=cls.company_a, status=Trip.ACTIVE, price=cls.price
        )

        cls.all_trips = cls.future_trips + cls.past_trips

        # For each trip create one available and two booked seats
        for trip in cls.all_trips:
            SeatFactory.reset_sequence(1)

            SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

            SeatFactory(trip=trip, seat_status=Seat.BOOKED)
            SeatFactory(trip=trip, seat_status=Seat.BOOKED)

    def test_all_trips_are_successfully_created(self):
        """Just check if all trips are present in DB"""

        qs = Trip.objects.all()

        self.assertEqual(qs.count(), len(self.all_trips))

        self.assertIn(self.future_active_trips_company_a[0], qs)
        self.assertIn(self.future_active_trips_company_a[1], qs)
        self.assertIn(self.future_active_trips_company_b[0], qs)
        self.assertIn(self.future_active_trips_company_b[1], qs)

        self.assertIn(self.future_inactive_trips[0], qs)
        self.assertIn(self.future_inactive_trips[1], qs)

        self.assertIn(self.past_trips[0], qs)
        self.assertIn(self.past_trips[1], qs)

    def test_future_manager_shows_only_future_trips_of_all_statuses(self):
        qs = Trip.future.all()

        self.assertEqual(qs.count(), len(self.future_trips))

        # Future active trips should be present
        self.assertIn(self.future_active_trips_company_a[0], qs)
        self.assertIn(self.future_active_trips_company_a[1], qs)

        self.assertIn(self.future_active_trips_company_b[0], qs)
        self.assertIn(self.future_active_trips_company_b[1], qs)

        # Future inactive trips should be present
        self.assertIn(self.future_inactive_trips[0], qs)
        self.assertIn(self.future_inactive_trips[1], qs)

        # Past trips should NOT be present
        self.assertNotIn(self.past_trips[0], qs)
        self.assertNotIn(self.past_trips[1], qs)

    def test_active_method_shows_only_active_trips_of_the_future(self):
        qs = Trip.future.active()

        self.assertEqual(qs.count(), 4)

        # Future active trips SHOULD be present
        self.assertIn(self.future_active_trips_company_a[0], qs)
        self.assertIn(self.future_active_trips_company_a[1], qs)

        self.assertIn(self.future_active_trips_company_b[0], qs)
        self.assertIn(self.future_active_trips_company_b[1], qs)

        # Future inactive trips SHOULD NOT be present
        self.assertNotIn(self.future_inactive_trips[0], qs)
        self.assertNotIn(self.future_inactive_trips[1], qs)

        # Past trips should NOT be present whether active or not
        self.assertNotIn(self.past_trips[0], qs)
        self.assertNotIn(self.past_trips[1], qs)

    def test_for_company_method_shows_future_active_trips_for_correct_company(self):
        """
        Here we need to make sure we are showing
            - results only for one company whose slug is provided
            - results are only future trips
            - results are only active trips
        """

        # We'll search for trips from company A only
        qs = Trip.future.for_company(company_slug=self.company_a.slug)

        self.assertEqual(qs.count(), len(self.future_active_trips_company_a))

        self.assertIn(self.future_active_trips_company_a[0], qs)
        self.assertIn(self.future_active_trips_company_a[1], qs)

        # Make sure company A's inactive trips are not shown
        self.assertNotIn(self.future_inactive_trips, qs)

        # Make sure company B's trips are not shown
        self.assertNotIn(self.future_active_trips_company_b[0], qs)
        self.assertNotIn(self.future_active_trips_company_b[1], qs)

        # Past trips should NOT be present whether active or not
        self.assertNotIn(self.past_trips[0], qs)
        self.assertNotIn(self.past_trips[1], qs)

        # Now let's search for company B only
        qs = Trip.future.for_company(company_slug=self.company_b.slug)

        self.assertEqual(qs.count(), len(self.future_active_trips_company_b))

        self.assertIn(self.future_active_trips_company_b[0], qs)
        self.assertIn(self.future_active_trips_company_b[1], qs)

    def test_for_company_method_annotates_trips_correctly(self):
        """
        Here we need to make sure the queryset is annotated with
            - availibiliy
            - occupancy
            - total
            - revenue
        """

        # We'll search for trips from company A only
        qs = Trip.future.for_company(company_slug=self.company_a.slug)

        self.assertEqual(qs.count(), len(self.future_active_trips_company_a))

        trip_1, trip_2 = qs

        # Check each trip has correct price
        self.assertEqual(trip_1.price, self.price)
        self.assertEqual(trip_2.price, self.price)

        # Check availability is annotated. We have 3 seats (1 available, 2 booked)
        self.assertEqual(trip_1.availability, 1)
        self.assertEqual(trip_2.availability, 1)

        # Check occupancy percentage is annotated. Should be 65 (i.e. 65% since 2/3)
        self.assertEqual(trip_1.occupancy, 65)
        self.assertEqual(trip_2.occupancy, 65)

        # Check revenue is annotated. Should be price * 2 since two tickets are booked
        revenue = self.price * 2
        self.assertEqual(trip_1.revenue, revenue)
        self.assertEqual(trip_2.revenue, revenue)

    def test_for_company_method_select_related_fields(self):
        """
        Make sure that while querying trips for a company we have prefetched the
            - company
            - origin
            - destination
        """

        trip_1, *rest = Trip.future.for_company(company_slug=self.company_a.slug)

        related_fields = trip_1._state.fields_cache
        self.assertIn("company", related_fields)
        self.assertIn("origin", related_fields)
        self.assertIn("destination", related_fields)


class FutureManagerSearchTests(TestCase):
    """
    Test suite to validate search results from future manager.

    We want to make sure while searching we get results filtered correctly for
        - origin
        - destination
        - departure
        - return (if provided)
    """

    @classmethod
    def setUpTestData(cls) -> None:
        # 1. Create three locations and a company
        cls.buenos_aires = LocationFactory(name="Buenos Aires")
        cls.mendoza = LocationFactory(name="Mendoza")
        cls.bariloche = LocationFactory(name="Bariloche")

        cls.company = CompanyFactory()

        # 2. Create helper dates as strings
        cls.today = cls.get_date()
        cls.tomorrow = cls.get_date(days=1)
        cls.day_after_tomorrow = cls.get_date(days=2)
        cls.yesterday = cls.get_date(days=-1)

        # 3. Create some past and future trips
        cls.trips_past = TripPastFactory.create_batch(
            size=2,
            origin=cls.buenos_aires,
            destination=cls.mendoza,
            status=Trip.ACTIVE,
            company=cls.company,
        )

        cls.trips_tomorrow = TripTomorrowFactory.create_batch(
            size=2,
            origin=cls.buenos_aires,
            destination=cls.mendoza,
            status=Trip.ACTIVE,
            company=cls.company,
        )

        cls.trips_day_after_tomorrow = TripDayAfterTomorrowFactory.create_batch(
            size=2,
            origin=cls.buenos_aires,
            destination=cls.mendoza,
            status=Trip.ACTIVE,
            company=cls.company,
        )

        cls.all_trips = (
            cls.trips_past + cls.trips_tomorrow + cls.trips_day_after_tomorrow
        )

        # For each trip create one available and two booked seats
        for trip in cls.all_trips:
            SeatFactory.reset_sequence(1)

            SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

            SeatFactory(trip=trip, seat_status=Seat.BOOKED)
            SeatFactory(trip=trip, seat_status=Seat.BOOKED)

    @classmethod
    def get_date(cls, days=0):
        custom_date = date.today() + timedelta(days=days)
        return custom_date.strftime("%d-%m-%Y")

    def test_trips_are_correctly_generated(self):
        self.assertEqual(Trip.objects.count(), 6)
        self.assertEqual(Trip.future.count(), 4)

    def test_search_raises_404_for_missing_fields(self):
        """
        Check if any of the query params is not supplied to the manager we should raise
        an http404
        """

        # Missing origin
        with self.assertRaises(Http404):
            Trip.future.search(
                origin=None, destination=self.mendoza.slug, departure=self.today
            )

        # Missing destination
        with self.assertRaises(Http404):
            Trip.future.search(
                origin=self.buenos_aires.slug, destination=None, departure=self.today
            )

        # Missing departure
        with self.assertRaises(Http404):
            Trip.future.search(
                origin=self.buenos_aires.slug,
                destination=self.mendoza.slug,
                departure=None,
            )

        # Missing all fields
        with self.assertRaises(Http404):
            Trip.future.search()

    def test_search_returns_valid_results_for_departure(self):
        """
        Here the idea is to play around with the departure date and check correct
        trips are returned.
        """

        # Get trips only tomorrow
        qs_tomorrow = Trip.future.search(
            origin=self.buenos_aires, destination=self.mendoza, departure=self.tomorrow
        )
        self.assertEqual(qs_tomorrow.count(), len(self.trips_tomorrow))

        # Get trips only for day after tomorrow
        qs_day_after_tomorrow = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.mendoza,
            departure=self.day_after_tomorrow,
        )
        self.assertEqual(
            qs_day_after_tomorrow.count(), len(self.trips_day_after_tomorrow)
        )

        # Get trips for past
        # Although we have past active trips make sure their are never returned by the manager
        qs_past = Trip.future.search(
            origin=self.buenos_aires, destination=self.mendoza, departure=self.yesterday
        )
        self.assertEqual(qs_past.count(), 0)

    def test_search_returns_zero_trips_for_no_trips_between_locations(self):
        """
        Here we have two valid locations but trips scheduled for any date.
        Make sure we get zero results.
        """

        qs = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.bariloche,
            departure=self.tomorrow,
        )
        self.assertEqual(qs.count(), 0)

        qs = Trip.future.search(
            origin=self.bariloche,
            destination=self.buenos_aires,
            departure=self.day_after_tomorrow,
        )
        self.assertEqual(qs.count(), 0)

    def test_search_does_not_return_trips_that_are_not_active(self):
        # Create an inactive trips for tomorrow

        invalid_statuses = [Trip.CANCELLED, Trip.ONHOLD, Trip.DELAYED, Trip.OTHER]

        _ = [
            TripTomorrowFactory(
                origin=self.buenos_aires,
                destination=self.bariloche,
                status=status,
            )
            for status in invalid_statuses
        ]

        # Search for trips between these locations for tomorrow
        # They exist but are not active
        qs = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.bariloche,
            departure=self.tomorrow,
        )

        # We should get zero results
        self.assertEqual(qs.count(), 0)

    def test_search_results_are_annotated_with_availability_attribute(self):
        """
        Here we need to make sure the queryset is annotated with
            - availibiliy
        """

        # Get trips only tomorrow
        qs = Trip.future.search(
            origin=self.buenos_aires, destination=self.mendoza, departure=self.tomorrow
        )
        self.assertEqual(qs.count(), len(self.trips_tomorrow))

        trip_1, trip_2, *rest = qs

        # Check availability is annotated. We have 3 seats (1 available, 2 booked)
        self.assertEqual(trip_1.availability, 1)
        self.assertEqual(trip_2.availability, 1)

    def test_search_results_contains_select_related_fields(self):
        """
        Make sure that while searching for trips we have prefetched the
            - company
            - origin
            - destination
        """

        qs = Trip.future.search(
            origin=self.buenos_aires, destination=self.mendoza, departure=self.tomorrow
        )

        trip_1, *rest = qs

        related_fields = trip_1._state.fields_cache

        self.assertIn("company", related_fields)
        self.assertIn("origin", related_fields)
        self.assertIn("destination", related_fields)

    def test_search_results_are_filtered_by_a_company(self):
        """
        Search results can be specified for only one company.
        Our test data is generated for only one company.
        """

        # Let's create one trip for another company
        another_company = CompanyFactory()
        another_trip = TripTomorrowFactory(
            origin=self.buenos_aires,
            destination=self.mendoza,
            company=another_company,
            status=Trip.ACTIVE,
        )

        # Get trips only tomorrow for another company
        qs_tomorrow = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.mendoza,
            departure=self.tomorrow,
            company_slug=another_company.slug,  # <-- added this
        )

        trip_found = qs_tomorrow.first()

        self.assertEqual(qs_tomorrow.count(), 1)
        self.assertEqual(trip_found, another_trip)
        self.assertEqual(trip_found.company, another_company)

    def test_search_results_are_ordered_correctly(self):
        Trip.objects.all().delete()

        d = timezone.now() + timedelta(days=1)

        morning = d.replace(hour=8)
        afternoon = d.replace(hour=13)
        evening = d.replace(hour=20)

        for departure in (morning, afternoon, evening):
            TripTomorrowFactory(
                origin=self.buenos_aires,
                destination=self.mendoza,
                departure=departure,
                status=Trip.ACTIVE,
            )

        # Make sure three trips in DB
        self.assertEqual(Trip.objects.count(), 3)

        # Get trips ordered by departure descending (latest by time)
        qs = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.mendoza,
            departure=self.tomorrow,
            ordering="-departure",  # <-- added this
        )

        self.assertEqual(qs.first().departure, evening)
        self.assertEqual(qs.last().departure, morning)

        # Get trips ordered by departure ascending (earliest by time)
        # This is also the default strategy
        qs = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.mendoza,
            departure=self.tomorrow,
            ordering="departure",  # <-- added this
        )

        self.assertEqual(qs.first().departure, morning)
        self.assertEqual(qs.last().departure, evening)

        # Get trips ordered by price ascending (cheapest)
        qs = Trip.future.search(
            origin=self.buenos_aires,
            destination=self.mendoza,
            departure=self.tomorrow,
            ordering="price",  # <-- added this
        )

        expected = min(Trip.objects.values_list("price", flat=True))
        actual = qs.first().price
        self.assertEqual(actual, expected)
