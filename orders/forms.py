from django import forms

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


class PassengerForm(forms.ModelForm):
    class Meta:
        model = Passenger
        exclude = ("trip", "created_on", "updated_on")

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
