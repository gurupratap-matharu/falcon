from django.test import SimpleTestCase

from coupons.forms import CouponApplyForm


class CouponApplyFormTests(SimpleTestCase):
    """
    Test suite to test the coupon apply form
    """

    def test_coupon_apply_form_is_invalid_for_invalid_data(self):
        form = CouponApplyForm(data={"code": "summer 20"})

        self.assertFalse(form.is_valid())

    def test_coupon_apply_form_is_valid_for_valid_data(self):
        form = CouponApplyForm(data={"code": "SUMMER20"})

        self.assertTrue(form.is_valid())
