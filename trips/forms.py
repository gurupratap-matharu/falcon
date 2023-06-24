import json
import logging
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from dateutil import rrule

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.errors:
            attrs = self[field].field.widget.attrs
            attrs.setdefault("class", "")
            attrs["class"] += " is-invalid"

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
                attrs={"class": "form-control", "required": "required"}
            ),
            "origin": forms.Select(
                attrs={"class": "form-select", "required": "required"}
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
            "price": forms.NumberInput(
                attrs={"class": "form-control", "required": "required"}
            ),
            "status": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "mode": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "(Optional)",
                    "cols": 80,
                    "rows": 5,
                }
            ),
        }


class RecurrenceForm(forms.Form):
    """
    Form to create multiple instances of an event based on dateutil rrules.
    """

    FREQUENCY_CHOICES = [
        (None, "----------"),
        (rrule.HOURLY, _("Every Hour")),
        (rrule.DAILY, _("Every Day")),
        (rrule.WEEKLY, _("Every Week")),
        (rrule.MONTHLY, _("Every Month")),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.errors:
            logger.info("field: %s has error" % field)
            attrs = self[field].field.widget.attrs
            attrs.setdefault("class", "")
            attrs["class"] += " is-invalid"

    dtstart = forms.DateTimeField(
        label=_("Starts"),
        initial=datetime.now,
        error_messages={"required": _("Please enter start date")},
        widget=forms.DateTimeInput(attrs={"class": "form-control"}),
    )

    freq = forms.ChoiceField(
        label=_("Repeats"),
        help_text=_("Frequency of the event (required)"),
        choices=FREQUENCY_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    until = forms.DateTimeField(
        label=_("End Repeat"),
        help_text=_("Provide either End repeat or Count."),
        required=False,
        widget=forms.DateTimeInput(attrs={"class": "form-control"}),
    )

    count = forms.IntegerField(
        label=_("Count"),
        help_text=_(
            "(Optional) End repeat after these many occurrences (between 0-1000). "
            "Provide either End repeat or Count."
        ),
        required=False,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    interval = forms.IntegerField(
        label=_("Interval"),
        initial=1,
        help_text=_(
            "(Optional) Time between consecutive occurrences. "
            "Ex for daily repeats 1: Every day, 2: Every other day, 3: every third day and so on..."
        ),
        required=False,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def _clean_dt(self, dt):
        """Make sure datetime is not in the past"""

        if dt and dt.date() < timezone.localdate():
            raise ValidationError(
                _("datetime (%(dt)s) cannot be in the past!"),
                code="invalid",
                params={"dt": dt.strftime("%d-%m-%Y %H:%M:%S")},
            )

        return dt

    def clean_dtstart(self):
        """Make sure start date is not in the past"""

        dtstart = self.cleaned_data["dtstart"]
        return self._clean_dt(dt=dtstart)

    def clean_until(self):
        """Make sure end date is not in the past"""

        until = self.cleaned_data["until"]
        return self._clean_dt(dt=until)

    def clean_freq(self):
        freq = self.cleaned_data["freq"]

        if not freq:
            return
        return int(freq)

    def clean(self):
        cleaned_data = super().clean()

        dtstart = cleaned_data.get("dtstart")
        until = cleaned_data.get("until")
        count = cleaned_data.get("count")

        # End date cannot be less than start date
        if dtstart and until and until < dtstart:
            msg = _("End time cannot be less than Start time.")
            self.add_error("until", msg)

        # Either until or count is needed
        if not until and not count:
            msg = _("Provide either End repeat or Count.")
            self.add_error("until", msg)
            self.add_error("count", msg)

    def save(self):
        logger.info("saving recurrence form...")

        occurrences = self.build_occurrence_timestamps()
        logger.info("Total occurrences: %s" % occurrences.count())
        logger.info("occurrences: %s" % occurrences)

        return occurrences

    def build_occurrence_timestamps(self):
        """
        Use the cleaned data as rrule params for the dateutil library and
        build a list of datetime objects which represent future occurrence timestamps.
        """

        cd = self.cleaned_data
        params = {k: v for k, v in cd.items() if v is not None}

        logger.info("params:%s" % params)
        logger.info("building occurrence timestamps...")

        return rrule.rrule(**params)
