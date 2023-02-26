from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

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

    def test_coupon_valid_from_date_cannot_be_in_the_past(self):
        yesterday = timezone.now() - timedelta(days=1)

        with self.assertRaises(ValidationError):
            c = CouponFactory.build(valid_from=yesterday)
            c.full_clean()  # <-- not called automatically on save

    def test_coupon_valid_to_date_cannot_be_less_than_valid_from_date(self):
        today = timezone.now()
        yesterday = today - timedelta(days=1)

        with self.assertRaises(ValidationError):
            c = CouponFactory.build(valid_from=today, valid_to=yesterday)
            c.full_clean()  # <-- not called automatically on save

    def test_coupon_discount_cannot_be_less_than_zero_or_more_than_hundred(self):

        with self.assertRaises(ValidationError):
            c = CouponFactory.build(discount=-1)
            c.full_clean()

        with self.assertRaises(ValidationError):
            c = CouponFactory.build(discount=101)
            c.full_clean()

    def test_deactivating_a_valid_coupon_works(self):
        today = timezone.now()
        tomorrow = today + timedelta(days=1)

        coupon = Coupon.objects.create(
            code="MENDOZA50",
            discount=50,
            valid_from=today,
            valid_to=tomorrow,
            active=True,
        )

        self.assertTrue(coupon.active)
        self.assertTrue(coupon.is_valid())

        coupon.deactivate()

        self.assertFalse(coupon.active)
        self.assertFalse(coupon.is_valid())

    def test_deactivating_an_inactive_coupon_raises_validation_error(self):
        today = timezone.now()
        tomorrow = today + timedelta(days=1)

        coupon = Coupon.objects.create(
            code="MENDOZA50",
            discount=50,
            valid_from=today,
            valid_to=tomorrow,
            active=False,  # <-- already redeemed coupon
        )

        self.assertFalse(coupon.active)
        self.assertFalse(coupon.is_valid())

        with self.assertRaises(ValidationError):
            coupon.deactivate()

        self.assertFalse(coupon.active)
        self.assertFalse(coupon.is_valid())
