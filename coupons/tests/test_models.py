from django.db import IntegrityError
from django.test import TestCase

from coupons.factories import CouponFactory
from coupons.models import Coupon


class CouponModelTests(TestCase):
    """Test suite for the Coupon Model"""

    def setUp(self) -> None:
        self.coupon = CouponFactory()

    def test_str_representation(self):
        self.assertEqual(str(self.coupon), f"{self.coupon.code}")

    def test_verbose_name_plural(self):
        self.assertEqual(str(self.coupon._meta.verbose_name_plural), "coupons")

    def test_coupon_model_creation_is_accurate(self):
        coupon_from_db = Coupon.objects.first()

        self.assertEqual(Coupon.objects.count(), 1)
        self.assertEqual(coupon_from_db.code, self.coupon.code)
        self.assertEqual(coupon_from_db.active, self.coupon.active)
        self.assertEqual(coupon_from_db.valid_from, self.coupon.valid_from)
        self.assertEqual(coupon_from_db.valid_to, self.coupon.valid_to)
        self.assertEqual(coupon_from_db.discount, self.coupon.discount)

    def test_coupon_code_max_length(self):
        coupon = Coupon.objects.first()
        max_length = coupon._meta.get_field("code").max_length  # type:ignore

        self.assertEqual(max_length, 50)

    def test_all_coupons_have_unique_codes(self):
        Coupon.objects.all().delete()

        c = CouponFactory(code="Mendoza10", discount=10)

        data = c.__dict__
        data.pop("_state")
        data.pop("id")

        with self.assertRaises(IntegrityError):
            # try to create the same coupon
            # veer here we use the objects.create since factory uses get_or_create on
            # code field so it will not try to create another coupon
            _ = Coupon.objects.create(**data)
