import logging

from django import forms

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
