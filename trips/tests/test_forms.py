from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase
from django.utils import timezone

from dateutil import rrule

from trips.factories import LocationFactory
from trips.forms import RecurrenceForm, TripSearchForm


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
