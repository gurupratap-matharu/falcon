from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class ProfileEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.errors:
            attrs = self[field].field.widget.attrs
            attrs.setdefault("class", "")
            attrs["class"] += " is-invalid"

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "bio", "location", "personal_website")
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "First name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Last name"}
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bio",
                    "cols": 80,
                    "rows": 5,
                }
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Location"}
            ),
            "personal_website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "Website"}
            ),
        }


class AccountDeleteForm(forms.Form):
    delete = forms.BooleanField(required=True)
