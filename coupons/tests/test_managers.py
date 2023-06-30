from django.test import TestCase

from coupons.factories import CouponInvalidFactory, CouponValidFactory
from coupons.models import Coupon


class ValidManagerTests(TestCase):
    """
    Test suite to validate manager for coupon model
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.valid_coupon = CouponValidFactory()
        cls.invalid_coupon = CouponInvalidFactory()

    def test_coupons_are_successfully_created(self):
        self.assertEqual(Coupon.objects.count(), 2)
        self.assertTrue(self.valid_coupon.is_valid())
        self.assertFalse(self.invalid_coupon.is_valid())

    def test_valid_manager_shows_only_valid_coupons(self):
        qs = Coupon.valid.all()

        self.assertEqual(qs.count(), 1)
        self.assertIn(self.valid_coupon, qs)
        self.assertNotIn(self.invalid_coupon, qs)
