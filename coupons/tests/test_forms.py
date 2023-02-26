from django.test import SimpleTestCase

from coupons.forms import CouponApplyForm


class CouponApplyFormTests(SimpleTestCase):
    """
    Test suite to test the coupon apply form
    """

    field_required_msg = "This field is required."

    def test_coupon_apply_form_is_invalid_for_missing_code(self):
        form = CouponApplyForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["code"][0], self.field_required_msg)

    def test_coupon_apply_form_is_valid_for_valid_data(self):
        form = CouponApplyForm(data={"code": "SUMMER20"})

        self.assertTrue(form.is_valid())
