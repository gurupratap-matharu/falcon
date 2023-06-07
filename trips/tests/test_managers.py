import pdb

from django.test import TestCase

from companies.factories import CompanyFactory
from trips.factories import SeatFactory, TripPastFactory, TripTomorrowFactory
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

    def test_search_method_filters_results_correctly(self):
        pass
