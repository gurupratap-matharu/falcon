from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase

from trips.factories import LocationFactory
from trips.forms import TripSearchForm


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
