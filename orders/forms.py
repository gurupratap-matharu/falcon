import datetime
import logging

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Order, Passenger

logger = logging.getLogger(__name__)


class OrderForm(forms.ModelForm):
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
    class Meta:
        model = Passenger
        exclude = ("created_on", "updated_on")

        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": "required",
                }
            ),
            "document_number": forms.TextInput(
                attrs={
                    "placeholder": "Document Number",
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "First Name",
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Last Name",
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "birth_date": forms.TextInput(
                attrs={
                    "placeholder": "Date of Birth [dd/mm/yyyy]",
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "Phone",
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "nationality": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "gender": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": "required",
                }
            ),
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
        """Make sure passenger age is 3-99 years old"""

        birth_date = self.cleaned_data["birth_date"]
        if birth_date > datetime.date.today():
            raise ValidationError(
                _("Your birth date (%(birth_date)s) cannot be in the future!"),
                code="invalid",
                params={"birth_date": birth_date},
            )

        return birth_date
