from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase
from django.utils import timezone

from dateutil import rrule

from trips.factories import LocationFactory, RouteFactory, StopFactory
from trips.forms import PriceGridForm, RecurrenceForm, TripCreateForm, TripSearchForm
from trips.models import Trip


class PriceGridFormTests(TestCase):
    """
    Test suite to check the functionality of the price grid form.
    """

    def setUp(self):
        self.route = RouteFactory()
        self.origin = StopFactory(route=self.route)
        self.destination = StopFactory(route=self.route)

    def test_price_grid_form_with_negative_price(self):
        data = {
            "origin": self.origin,
            "destination": self.destination,
            "price": -1,  # invalid price
        }

        form = PriceGridForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors, {"price": ["Ensure this value is greater than or equal to 0."]}
        )

    def test_price_grid_form_with_very_high_price(self):
        data = {
            "origin": self.origin,
            "destination": self.destination,
            "price": 500000,  # invalid price
        }

        form = PriceGridForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"price": ["Ensure this value is less than or equal to 100000."]},
        )

    def test_price_grid_form_with_same_origin_destination_raises_error(self):
        data = {
            "origin": self.origin,
            "destination": self.origin,  # invalid
            "price": 100,
        }

        form = PriceGridForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"destination": ["origin and destination cannot be the same."]},
        )

    def test_price_grid_form_save_updates_route_price_correctly(self):
        # create route with empty price dict
        route = RouteFactory(price=dict())
        self.assertEqual(route.price, {})

        # create a valid form
        data = {"origin": self.origin, "destination": self.destination, "price": 100}
        form = PriceGridForm(data=data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

        # build the expected price dict
        key = f"{self.origin.name.abbr.strip()};{self.destination.name.abbr.strip()}"
        expected_price = {key: 100}

        # save the form and it should update route price correctly
        form.save(route=route)
        route.refresh_from_db()

        self.assertEqual(route.price, expected_price)


class TripSearchFormTests(TestCase):
    """
    Test suite to validate the home page search form.
    """

    @classmethod
    def setUpTestData(cls):
        cls.origin = LocationFactory(name="Buenos Aires")
        cls.destination = LocationFactory(name="Mendoza")

    def test_invalid_origin_raises_exception(self):
        today = datetime.today()
        departure = (today - timedelta(days=1)).strftime("%d-%m-%Y")

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["India"],  # <- invalid origin
            "destination": ["Mendoza"],
            "departure": [departure],
            "return": [""],
        }

        form = TripSearchForm(data=data)

        with self.assertRaises(Http404):
            form.validate()

    def test_invalid_destination_raises_exception(self):
        today = datetime.today()
        departure = (today - timedelta(days=1)).strftime("%d-%m-%Y")

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["India"],  # <- invalid destination
            "departure": [departure],
            "return": [""],
        }

        form = TripSearchForm(data=data)

        with self.assertRaises(Http404):
            form.validate()

    def test_missing_origin_or_destination_raises_exception(self):
        today = datetime.today()
        departure = (today - timedelta(days=1)).strftime("%d-%m-%Y")

        data_without_origin = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": [""],
            "destination": ["Mendoza"],
            "departure": [departure],
            "return": [],
        }

        data_without_destination = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": [""],
            "departure": [departure],
            "return": [],
        }

        form_1 = TripSearchForm(data=data_without_origin)
        form_2 = TripSearchForm(data=data_without_destination)

        with self.assertRaises(Http404):
            form_1.validate()

        with self.assertRaises(Http404):
            form_2.validate()

    def test_invalid_departure_date_raises_exception(self):
        """
        Departure date is in the past and this should raise an exception.
        """

        today = datetime.today()
        departure = (today - timedelta(days=1)).strftime("%d-%m-%Y")

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [departure],
            "return": [""],
        }

        form = TripSearchForm(data=data)

        with self.assertRaises(ValidationError):
            form.validate()

    def test_missing_departure_date_raises_exception(self):
        """
        Departure date is missing and this should raise an exception.
        """

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [],
            "return": [""],
        }

        form = TripSearchForm(data=data)

        with self.assertRaises(ValidationError):
            form.validate()

    def test_invalid_return_date_raises_exception(self):
        """
        Return date is before the departure date. This should raise an exception
        """

        today = datetime.today()
        departure = today.strftime("%d-%m-%Y")

        # return date is earlier than departure and in the past
        return_date = (today - timedelta(days=1)).strftime("%d-%m-%Y")

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [departure],
            "return": [return_date],
        }

        form = TripSearchForm(data=data)

        with self.assertRaises(ValidationError):
            form.validate()

    def test_valid_form_with_return_date(self):
        """
        No exception should be raised and the test should just pass
        So nothing to assert here.
        """

        today = datetime.today()
        departure = today.strftime("%d-%m-%Y")
        return_date = (today + timedelta(days=1)).strftime("%d-%m-%Y")

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [departure],
            "return": [return_date],
        }

        form = TripSearchForm(data=data)
        form.validate()

    def test_valid_form_without_return_date(self):
        """
        No exception should be raised and the test should just pass
        So nothing to assert here.
        """

        today = datetime.today()
        departure = today.strftime("%d-%m-%Y")

        data = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [departure],
            "return": [],
        }

        form = TripSearchForm(data=data)
        form.validate()

    def test_invalid_num_of_passengers_raises_exception(self):
        today = datetime.today().strftime("%d-%m-%Y")

        data_1 = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["11"],  # <- invalid number as > 10
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [today],
            "return": [],
        }

        data_2 = {
            "trip_type": ["round_trip"],
            "num_of_passengers": ["0"],  # <- invalid number
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [today],
            "return": [],
        }

        form_1 = TripSearchForm(data=data_1)
        form_2 = TripSearchForm(data=data_2)

        with self.assertRaises(ValidationError):
            form_1.validate()

        with self.assertRaises(ValidationError):
            form_2.validate()

    def test_invalid_trip_type_raises_exception(self):
        today = datetime.today().strftime("%d-%m-%Y")

        data_1 = {
            "trip_type": ["solo"],  # <- invalid string
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [today],
            "return": [],
        }

        data_2 = {
            "trip_type": [""],  # <- missing trip type
            "num_of_passengers": ["1"],
            "origin": ["Buenos Aires"],
            "destination": ["Mendoza"],
            "departure": [today],
            "return": [],
        }

        form_1 = TripSearchForm(data=data_1)
        form_2 = TripSearchForm(data=data_2)

        with self.assertRaises(ValidationError):
            form_1.validate()

        with self.assertRaises(ValidationError):
            form_2.validate()


class TripCreateFormTests(TestCase):
    """
    Test suite to validate trip creation model form.
    """

    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()
        cls.yesterday = cls.now - timedelta(days=1)
        cls.tomorrow = cls.now + timedelta(days=1)
        cls.day_after = cls.now + timedelta(days=2)

        cls.origin = LocationFactory(name="Buenos Aires")
        cls.destination = LocationFactory(name="Mendoza")

    def test_trip_create_form_is_valid_for_valid_data(self):
        data = {
            "name": "demo trip",
            "origin": self.origin,
            "destination": self.destination,
            "departure": self.tomorrow,
            "arrival": self.day_after,
            "price": 10,
            "status": Trip.ACTIVE,
            "mode": Trip.DIRECT,
        }

        form = TripCreateForm(data=data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_trip_create_form_is_invalid_for_departure_in_past(self):
        data = {
            "name": "demo trip",
            "origin": self.origin,
            "destination": self.destination,
            "departure": self.yesterday,  # <-- departure in past
            "arrival": self.day_after,
            "price": 10,
            "status": Trip.ACTIVE,
            "mode": Trip.DIRECT,
        }

        form = TripCreateForm(data=data)
        self.assertFalse(form.is_valid())

        error_msg = ["Departure cannot be in the past!"]
        self.assertEqual(form.errors["departure"], error_msg)

    def test_trip_create_form_is_invalid_for_arrival_earlier_than_departure(self):
        data = {
            "name": "demo trip",
            "origin": self.origin,
            "destination": self.destination,
            "departure": self.day_after,
            "arrival": self.tomorrow,  # <- arrival earlier than departure
            "price": 10,
            "status": Trip.ACTIVE,
            "mode": Trip.DIRECT,
        }

        form = TripCreateForm(data=data)
        self.assertFalse(form.is_valid())

        error_msg = ["Arrival cannot be earlier than departure!"]
        self.assertEqual(form.errors["arrival"], error_msg)

    def test_trip_create_form_throws_error_for_same_origin_and_destination(self):
        data = {
            "name": "demo trip",
            "origin": self.origin,
            "destination": self.origin,  # <- destination same as origin (invalid)
            "departure": self.tomorrow,
            "arrival": self.day_after,
            "price": 10,
            "status": Trip.ACTIVE,
            "mode": Trip.DIRECT,
        }

        form = TripCreateForm(data=data)

        error_msg = ["origin and destination cannot be same"]

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["origin"], error_msg)
        self.assertEqual(form.errors["destination"], error_msg)


class RecurrenceFormTests(TestCase):
    """
    Test suite to validate the recurrence form.
    """

    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()

        cls.yesterday = cls.now - timedelta(days=1)
        cls.tomorrow = cls.now + timedelta(days=1)
        cls.day_after = cls.now + timedelta(days=2)
        cls.next_week = cls.now + timedelta(days=7)
        cls.next_month = cls.now + timedelta(days=31)
        cls.next_year = cls.now + timedelta(days=365)

    def test_recurrence_form_is_valid_for_valid_data(self):
        data = {"dtstart": self.tomorrow, "until": self.day_after, "freq": rrule.DAILY}
        form = RecurrenceForm(data)

        self.assertTrue(form.is_valid())

    def test_recurrence_form_is_invalid_missing_start_date(self):
        data = {"until": self.day_after, "freq": rrule.MONTHLY}
        form = RecurrenceForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"dtstart": ["Please enter start date"]})

    def test_recurrence_form_is_invalid_for_past_start_date(self):
        ts = self.yesterday.strftime("%d-%m-%Y %H:%M:%S")
        data = {
            "dtstart": self.yesterday,
            "until": self.day_after,
            "freq": rrule.HOURLY,
        }
        form = RecurrenceForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"dtstart": [f"datetime ({ts}) cannot be in the past!"]},
        )

    def test_recurrence_form_is_invalid_for_past_end_date(self):
        ts = self.yesterday.strftime("%d-%m-%Y %H:%M:%S")
        data = {"dtstart": self.tomorrow, "until": self.yesterday, "freq": rrule.WEEKLY}
        form = RecurrenceForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["until"],
            [
                f"datetime ({ts}) cannot be in the past!",
                "Provide either End repeat or Count.",
            ],
        )

    def test_recurrence_form_is_invalid_if_both_count_and_until_are_missing(self):
        data = {"dtstart": self.tomorrow, "freq": rrule.DAILY}
        form = RecurrenceForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "until": ["Provide either End repeat or Count."],
                "count": ["Provide either End repeat or Count."],
            },
        )

    def test_recurrence_form_is_invalid_if_end_date_is_less_than_start_date(self):
        data = {"dtstart": self.day_after, "until": self.tomorrow, "freq": rrule.DAILY}
        form = RecurrenceForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors, {"until": ["End time cannot be less than Start time."]}
        )

    def test_recurrence_form_is_invalid_missing_frequency(self):
        data = {"dtstart": self.tomorrow, "until": self.day_after}
        form = RecurrenceForm(data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"freq": ["This field is required."]})

    # Test valid creation
    # Hourly
    def test_hourly_recurrence_until_date(self):
        params = {
            "dtstart": self.tomorrow,
            "until": self.day_after,
            "freq": rrule.HOURLY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_hourly_recurrence_with_count(self):
        params = {
            "dtstart": self.tomorrow,
            "count": 5,
            "freq": rrule.HOURLY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_hourly_recurrence_with_interval(self):
        params = {
            "dtstart": self.tomorrow,
            "until": self.day_after,
            "freq": rrule.HOURLY,
            "interval": 3,  # every three hours
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    # Daily
    def test_daily_recurrence_until_date(self):
        params = {
            "dtstart": self.tomorrow,
            "until": self.next_week,
            "freq": rrule.DAILY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_daily_recurrence_with_count(self):
        params = {
            "dtstart": self.tomorrow,
            "count": 5,
            "freq": rrule.DAILY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_daily_recurrence_with_interval(self):
        params = {
            "dtstart": self.tomorrow,
            "until": self.next_month,
            "freq": rrule.DAILY,
            "interval": 2,  # every other day
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    # Weekly
    def test_weekly_recurrence_until_date(self):
        params = {
            "dtstart": self.tomorrow,
            "until": self.next_month,
            "freq": rrule.WEEKLY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_weekly_recurrence_with_count(self):
        params = {
            "dtstart": self.tomorrow,
            "count": 25,
            "freq": rrule.WEEKLY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_weekly_recurrence_with_interval(self):
        params = {
            "dtstart": self.tomorrow,
            "count": 25,
            "freq": rrule.WEEKLY,
            "interval": 2,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    # Monthly
    def test_monthly_recurrence_until_date(self):
        params = {
            "dtstart": self.tomorrow,
            "until": self.next_year,
            "freq": rrule.MONTHLY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_monthly_recurrence_with_count(self):
        params = {
            "dtstart": self.tomorrow,
            "count": 24,
            "freq": rrule.MONTHLY,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)

    def test_monthly_recurrence_with_interval(self):
        params = {
            "dtstart": self.tomorrow,
            "count": 36,
            "freq": rrule.MONTHLY,
            "interval": 2,
        }

        form = RecurrenceForm(params)
        actual = list(form.build_occurrence_timestamps())
        expected = list(rrule.rrule(**params))

        self.assertEqual(actual, expected)
