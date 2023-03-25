from datetime import timedelta
from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy
from django.utils import timezone

from coupons.models import Coupon
from coupons.views import coupon_apply


class CouponApplyViewTests(TestCase):
    """
    Test suite to verify application of coupon.
    """

    url = reverse_lazy("coupons:apply")

    def test_coupon_apply_url_resolve_coupon_apply_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, coupon_apply.__name__)

    def test_coupon_apply_view_accepts_only_post(self):

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_valid_coupon_code_is_successfully_applied(self):
        # Arrange
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

        # Act
        # Hit a post request with our valid coupon code
        response = self.client.post(self.url, data={"code": coupon.code})

        coupon.refresh_from_db()

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Check that a confirmation message is included in the response
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Coupon applied successfully! 📮")

        # Verify that coupon is deactivated and invalid now
        self.assertFalse(coupon.active)
        self.assertFalse(coupon.is_valid())

        # Verify that coupon is stored in the user session
        session = self.client.session
        self.assertIn("coupon_id", session)
        self.assertEqual(session["coupon_id"], coupon.id)
        self.assertIsNotNone(session["coupon_id"])

    def test_invalid_coupon_code_is_not_applied(self):
        # Arrange
        today = timezone.now()
        tomorrow = today + timedelta(days=1)

        coupon = Coupon.objects.create(
            code="MENDOZA50",
            discount=50,
            valid_from=today,
            valid_to=tomorrow,
            active=False,  # 👈 expired coupon
        )

        self.assertFalse(coupon.active)
        self.assertFalse(coupon.is_valid())

        # Act
        # Hit a post request with our valid coupon code
        response = self.client.post(self.url, data={"code": coupon.code})

        coupon.refresh_from_db()

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Check that a failure message is included in the response
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Coupon is invalid 🤕")

        # Verify that the coupon remains invalid
        self.assertFalse(coupon.active)
        self.assertFalse(coupon.is_valid())

        # Verify that no coupon is stored in user session
        session = self.client.session
        self.assertIn("coupon_id", session)
        self.assertNotEqual(session["coupon_id"], coupon.id)
        self.assertIsNone(session["coupon_id"])

    def test_valid_coupon_code_cannot_be_applied_multiple_times(self):
        # TODO: Please implement this!
        pass


class CouponListViewTests(TestCase):
    # TODO: PLEASE IMPLEMENT
    pass
