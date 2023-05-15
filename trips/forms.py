import json
import logging
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from trips.models import Location

from .models import Trip

logger = logging.getLogger(__name__)


class TripSearchForm:
    """
    Dummy class used to validate the homepage trip search form.

    We are not using django form for the main form as we don't know how to couple it
    with
        - autocomplete Js to show dynamic search results for locations
        - flatpickr to launch calendar for departure and return

    But we do need to validate the form one way or the other.
    This class does just that.
    """

    VALID_TRIP_TYPES = ("round_trip", "one_way")
    VALID_NUM_PASSENGERS = 10

    def __init__(self, data: QueryDict | dict[str, list[str]]):
        self.data = data or {}

    def validate(self):
        logger.info("validating search form...")

        self.clean_origin()
        self.clean_destination()
        self.clean_departure()
        self.clean_return()
        self.clean_num_passengers()
        self.clean_trip_type()

    def clean_origin(self):
        """Only allow origins present in our database"""

        logger.info("cleaning origin...")

        origin = self.data.get("origin")

        if isinstance(origin, list):
            origin = origin[0]

        return get_object_or_404(Location, name__iexact=origin)

    def clean_destination(self):
        """Only allow destinations present in our database"""

        logger.info("cleaning destination...")

        destination = self.data.get("destination")

        if isinstance(destination, list):
            destination = destination[0]

        return get_object_or_404(Location, name__iexact=destination)

    def clean_departure(self):
        """
        Make sure departure is not in the past and is supplied
        """

        logger.info("cleaning departure...")

        departure = self.data.get("departure")

        if not departure:
            raise ValidationError(_("Departure date is invalid"))

        if isinstance(departure, list):
            departure = departure[0]

        self.departure_date = datetime.strptime(departure, "%d-%m-%Y").date()

        if self.departure_date < datetime.today().date():
            raise ValidationError(_("Departure cannot be in the past!"))

    def clean_return(self):
        """
        Don't allow return date to be less than departure date
        Note: Return date is optional in our form.
        """

        logger.info("cleaning return...")

        today = datetime.today().date()
        departure_date = self.departure_date
        return_date = self.data.get("return")

        if not return_date:
            return

        if isinstance(return_date, list):
            return_date = return_date[0]

        return_date = datetime.strptime(return_date, "%d-%m-%Y").date()

        if (return_date < departure_date) or (return_date < today):
            raise ValidationError(
                _("Return date is invalid"),
            )

    def clean_trip_type(self):
        """
        Only allow trip types to be in self.VALID_TRIP_TYPES
        """

        logger.info("cleaning trip type...")

        trip_type = self.data.get("trip_type")

        if not trip_type:
            raise ValidationError(_("Trip type is not valid"))

        if isinstance(trip_type, list):
            trip_type = trip_type[0]

        if trip_type not in self.VALID_TRIP_TYPES:  # type:ignore
            raise ValidationError(_("Trip type is not valid"))

    def clean_num_passengers(self):
        """
        Only allow num of passengers to be <= self.VALID_NUM_PASSENGERS
        """

        logger.info("cleaning num passengers...")

        num_of_passengers = self.data.get("num_of_passengers")

        if not num_of_passengers:
            raise ValidationError(_("Number of passengers is not valid"))

        if isinstance(num_of_passengers, list):
            num_of_passengers = num_of_passengers[0]

        num_of_passengers = int(num_of_passengers)  # type:ignore

        if num_of_passengers < 1 or num_of_passengers > self.VALID_NUM_PASSENGERS:
            raise ValidationError(_("Number of passengers is not valid"))

    def __repr__(self):
        return json.dumps(self.data)


class TripCreateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = (
            "name",
            "origin",
            "destination",
            "departure",
            "arrival",
            "price",
            "status",
            "mode",
            "description",
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "origin": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": "required",
                },
            ),
            "destination": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "departure": forms.DateTimeInput(
                format="%Y-%m-%d %H:%M:%S", attrs={"class": "form-control departure"}
            ),
            "arrival": forms.DateTimeInput(
                format="%Y-%m-%d %H:%M:%S", attrs={"class": "form-control arrival"}
            ),
            "price": forms.TextInput(
                attrs={
                    "class": "form-select",
                    "required": "required",
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "mode": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-select",
                    "placeholder": "(Optional)",
                    "cols": 80,
                    "rows": 5,
                }
            ),
        }
