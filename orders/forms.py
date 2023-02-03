from django import forms
from django.forms.models import inlineformset_factory

from .models import Order, Passenger


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


PassengerFormset = inlineformset_factory(
    parent_model=Order,
    model=Passenger,
    fields=("document_type", "document_number"),
    extra=1,
    can_delete=True,
)
