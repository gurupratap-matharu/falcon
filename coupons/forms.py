from django import forms


class CouponApplyForm(forms.Form):
    """Simple form to allow a user to apply a coupon to the cart"""

    code = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Code", "class": "form-control"})
    )
