from django import forms
from django.utils.translation import gettext_lazy as _

from coupons.models import Coupon


class CouponApplyForm(forms.Form):
    """Simple form to allow a user to apply a coupon to the cart"""

    code = forms.CharField(
        label=_("coupon"),
        widget=forms.TextInput(
            attrs={"placeholder": _("Code"), "class": "form-control"}
        ),
    )


class CouponForm(forms.ModelForm):
    """Model form to create a new coupon"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.errors:
            attrs = self[field].field.widget.attrs
            attrs.setdefault("class", "")
            attrs["class"] += " is-invalid"

    class Meta:
        model = Coupon
        fields = ("code", "discount", "valid_from", "valid_to")
        attrs = {"class": "form-control"}
        dt_format = "%Y-%m-%d %H:%M:%S"
        widgets = {
            "code": forms.TextInput(attrs=attrs),
            "discount": forms.NumberInput(attrs=attrs),
            "valid_from": forms.DateTimeInput(attrs=attrs),
            "valid_to": forms.DateTimeInput(attrs=attrs),
        }
