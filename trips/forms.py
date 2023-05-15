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

    def __init__(self, data: QueryDict | dict[str, list[str]]):
        self.data = data or {}

    def validate(self):
        logger.info("validating search form...")

        self.clean_origin()
        self.clean_destination()
        self.clean_departure()
        self.clean_return()

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
        Make sure departure is not in the past
        """

        logger.info("cleaning departure...")

        departure = self.data.get("departure")
        if isinstance(departure, list):
            departure = departure[0]

        self.departure_date = datetime.strptime(departure, "%d-%m-%Y").date()

        if self.departure_date < datetime.today().date():
            raise ValidationError("Departure cannot be in the past!")

    def clean_return(self):
        """
        Don't allow return date to be less than departure date
        """

        logger.info("cleaning return...")

        return_date = self.data.get("return")
        if isinstance(return_date, list):
            return_date = return_date[0]

        if not return_date:
            return

        self.return_date = datetime.strptime(return_date, "%d-%m-%Y").date()

        if self.return_date < self.departure_date:
            raise ValidationError(
                _("Return date cannot be less than departure date"),
            )

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
