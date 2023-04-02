from django.test import TestCase

from companies.factories import CompanyFactory
from trips.factories import SeatFactory, TripPastFactory, TripTomorrowFactory
from trips.models import Seat, Trip
from users.factories import CompanyOwnerFactory


class FutureManagerTests(TestCase):
    """
    Test suite for check all methods of future manager of trip model

        get_queryset()
        active()
        search()
        for_company()

    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)

        # Create two active trips in the future
        cls.trips = TripTomorrowFactory.create_batch(
            size=2, company=cls.company, status=Trip.ACTIVE
        )
        # Create two cancelled trips in the future
        cls.inactive_trips = TripTomorrowFactory.create_batch(
            size=2, company=cls.company, status=Trip.CANCELLED
        )
        # Create two past trips
        cls.past_trips = TripPastFactory.create_batch(
            size=2, company=cls.company, status=Trip.ACTIVE
        )

        all_trips = cls.trips + cls.inactive_trips + cls.past_trips

        # Create one booked, one available seat for each trip
        for trip in all_trips:
            SeatFactory.reset_sequence(1)
            SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)
            SeatFactory(trip=trip, seat_status=Seat.BOOKED)

    def test_all_trips_are_successfully_created(self):
        qs = Trip.objects.all()

        self.assertEqual(qs.count(), 6)

        self.assertIn(self.trips[0], qs)
        self.assertIn(self.trips[1], qs)

        self.assertIn(self.inactive_trips[0], qs)
        self.assertIn(self.inactive_trips[1], qs)

        self.assertIn(self.past_trips[0], qs)
        self.assertIn(self.past_trips[1], qs)

    def test_future_manager_shows_only_future_trips_of_all_statuses(self):
        qs = Trip.future.all()

        self.assertEqual(qs.count(), 4)

        self.assertIn(self.trips[0], qs)
        self.assertIn(self.trips[1], qs)

        self.assertIn(self.inactive_trips[0], qs)
        self.assertIn(self.inactive_trips[1], qs)

        self.assertNotIn(self.past_trips[0], qs)
        self.assertNotIn(self.past_trips[1], qs)

    def test_active_method_shows_only_active_trips_of_the_future(self):
        qs = Trip.future.active()

        self.assertEqual(qs.count(), 2)

        self.assertIn(self.trips[0], qs)
        self.assertIn(self.trips[1], qs)

        self.assertNotIn(self.inactive_trips[0], qs)
        self.assertNotIn(self.inactive_trips[1], qs)

        self.assertNotIn(self.past_trips[0], qs)
        self.assertNotIn(self.past_trips[1], qs)


class FutureSearchManagerTests(TestCase):
    """
    Here we test only the search method of our future manager
    """

    def test_search_method_filters_results_correctly(self):
        pass

    # Check query annotations here as well


class FutureCompanyManagerTests(TestCase):
    """
    Here we test only the for_company() method of our future manager
    """

    def test_for_company_method_filters_results_only_for_a_company(self):
        pass

    # Check query annotations here as well
