import logging
from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Order, Passenger

logger = logging.getLogger(__name__)


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.errors:
            attrs = self[field].field.widget.attrs
            attrs.setdefault("class", "")
            attrs["class"] += " is-invalid"

    class Meta:
        model = Order
        fields = ("name", "email", "residence")

        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Name", "class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "Email", "class": "form-control"}
            ),
            "residence": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_name(self):
        """Make sure order name is title case"""

        raw_name = self.cleaned_data["name"]
        cleaned_name = raw_name.title()

        logger.info("OrderForm: cleaning name: %s -> %s" % (raw_name, cleaned_name))

        return cleaned_name

    def clean_email(self):
        """Make sure order email is lower case"""

        raw_email = self.cleaned_data["email"]
        cleaned_email = raw_email.lower()

        logger.info("OrderForm: cleaning email: %s -> %s" % (raw_email, cleaned_email))

        return cleaned_email


class PassengerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.errors:
            attrs = self[field].field.widget.attrs
            attrs.setdefault("class", "")
            attrs["class"] += " is-invalid"

    class Meta:
        model = Passenger
        exclude = ("created_on", "updated_on")

        select = {"class": "form-select", "required": "required"}
        control = {"class": "form-control", "required": "required"}
        widgets = {
            "document_type": forms.Select(attrs=select),
            "document_number": forms.TextInput(
                attrs={"placeholder": "Document Number", **control}
            ),
            "first_name": forms.TextInput(
                attrs={"placeholder": "First Name", **control}
            ),
            "last_name": forms.TextInput(attrs={"placeholder": "Last Name", **control}),
            "birth_date": forms.DateInput(
                attrs={"input_type": "date", "placeholder": "Date of Birth", **control}
            ),
            "phone_number": forms.TextInput(
                attrs={"placeholder": "Phone", "type": "tel", **control}
            ),
            "nationality": forms.Select(attrs=select),
            "gender": forms.Select(attrs=select),
        }

    def clean_first_name(self):
        """Make sure passenger first name is title case"""

        raw_name = self.cleaned_data["first_name"]
        cleaned_name = raw_name.title()

        logger.info(
            "PassengerForm: cleaning first_name: %s -> %s" % (raw_name, cleaned_name)
        )

        return cleaned_name

    def clean_last_name(self):
        """Make sure passenger last name is title case"""

        raw_name = self.cleaned_data["last_name"]
        cleaned_name = raw_name.title()

        logger.info(
            "PassengerForm: cleaning last_name: %s -> %s" % (raw_name, cleaned_name)
        )

        return cleaned_name

    def clean_birth_date(self):
        """
        Make sure passenger age is 1-99 years old
        # TODO: Veer you might remove this method as we are validating the birth date
        of a passenger using validators in the model field.
        """

        birth_date = self.cleaned_data["birth_date"]

        today = timezone.now().date()
        century_ago = today - timedelta(days=36500)

        if not (century_ago < birth_date < today):
            raise ValidationError(
                _("Your birth date (%(birth_date)s) is invalid!"),
                code="invalid",
                params={"birth_date": birth_date},
            )

        return birth_date
