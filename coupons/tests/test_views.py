from datetime import timedelta
from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy
from django.utils import timezone

from companies.factories import CompanyFactory
from coupons.forms import CouponForm
from coupons.models import Coupon
from coupons.views import CouponCreateView, coupon_apply
from users.factories import (
    CompanyOwnerFactory,
    StaffuserFactory,
    SuperuserFactory,
    UserFactory,
)


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


class CouponCreateViewTests(TestCase):
    """
    Test suite to check coupon create view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.url = reverse_lazy("companies:coupon-create", args=[cls.company.slug])
        cls.login_url = reverse_lazy("account_login")
        cls.template_name = "coupons/coupon_form.html"

    def test_coupon_create_url_resolves_correct_view(self):
        url = reverse_lazy("companies:coupon-create", args=[self.company.slug])
        view = resolve(url)

        self.assertEqual(view.func.__name__, CouponCreateView.as_view().__name__)

    def test_coupon_create_view_redirects_to_login_for_anonymous_user(self):
        # access the url without logging in.
        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_coupon_create_view_is_not_accessible_by_staff_user(self):
        # ARRANGE
        # Create a staff user
        user = StaffuserFactory()
        self.client.force_login(user)

        # Let him / her try to access first company's url
        response = self.client.get(self.url)

        # Assert user is correctly authenticated and a staff user
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is NOT given access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_coupon_create_view_is_not_accessible_by_logged_in_normal_public_user(self):
        # ARRANGE
        # Create a public user
        user = UserFactory()
        self.client.force_login(user)

        # Let him / her try to access first company's url
        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is NOT given access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_coupon_create_view_is_not_accessible_by_another_company_owner(self):
        # ARRANGE
        # Create a random company owner
        another_owner = CompanyOwnerFactory()
        self.client.force_login(another_owner)

        # Let him / her try to access first company's url
        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(another_owner.is_superuser)
        self.assertFalse(another_owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is NOT given access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_coupon_create_view_is_accessible_by_company_owner(self):
        """
        Check if a company owner can access the coupon create page from their admin.
        """
        user = self.owner
        self.client.force_login(user)

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertEqual(user, self.company.owner)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Coupon")
        self.assertContains(response, "Create")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert form in response
        self.assertIsInstance(response.context["form"], CouponForm)

        # Assert context is correctly built
        company = response.context["company"]
        self.assertEqual(company, self.company)

    def test_coupon_create_view_works_on_successful_post(self):
        """
        This is an end-to-end test for coupon creation.
        """
        # ARRANGE
        # Create valid post data
        now = timezone.now()

        tomorrow = now + timedelta(days=1)
        next_week = now + timedelta(days=7)

        tomorrow_str = tomorrow.strftime("%Y-%m-%d %H:%m")
        next_week_str = next_week.strftime("%Y-%m-%d %H:%m")

        code, discount = "WINTER100", 20

        data = dict(
            code=code,
            valid_from=tomorrow_str,
            valid_to=next_week_str,
            discount=discount,
        )

        self.client.force_login(self.owner)

        # ACT
        # Hit the endpoint with post
        # Creation will redirect to coupon list so make sure `follow=True`
        response = self.client.post(path=self.url, data=data, follow=True)

        # ASSERT
        # Get coupon created in DB
        coupon = Coupon.objects.first()

        self.assertEqual(Coupon.objects.count(), 1)

        # Verify redirection
        expected_url = self.company.get_coupon_list_url()
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        self.assertEqual(coupon.code, code)
        self.assertEqual(coupon.discount, discount)
        self.assertEqual(coupon.valid_from.date(), tomorrow.date())
        self.assertEqual(coupon.valid_to.date(), next_week.date())

        # Verify content of final redirected page
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Verify coupon creation success message on final page.

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), CouponCreateView.success_message)
