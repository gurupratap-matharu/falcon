import logging

from django import forms

from .models import Trip

logger = logging.getLogger(__name__)


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
            "image",
            "description",
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Name",
                    "class": "form-control",
                    "required": "required",
                }
            ),
            "origin": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
            "destination": forms.Select(
                attrs={"class": "form-select", "required": "required"}
            ),
        }
