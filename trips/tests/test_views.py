from http import HTTPStatus

from django.test import TestCase
from django.urls import resolve, reverse_lazy

from companies.factories import CompanyFactory
from trips.factories import TripFactory
from trips.views import TripCreateView, TripDetailView, TripListView
from users.factories import (
    CompanyOwnerFactory,
    StaffuserFactory,
    SuperuserFactory,
    UserFactory,
)


class TripListViewTests(TestCase):
    """
    Test suite for trip list view.
    """

    def setUp(self):
        self.url = reverse_lazy("trips:trip-list")
        self.response = self.client.get(self.url)
        self.template_name = "trips/trip_list.html"

    def test_trip_list_works_for_anonymous_user(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, "Results")
        self.assertNotContains(self.response, "Hi there. I should not be on this page.")

    def test_trip_list_url_resolve_triplistview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripListView.as_view().__name__)


class TripDetailViewTests(TestCase):
    """Test Suite for Trip DetailView"""

    def setUp(self):
        self.trip = TripFactory()
        self.url = self.trip.get_absolute_url()
        self.template_name = "trips/trip_detail.html"
        self.response = self.client.get(self.url)

    def test_trip_detail_view_works_correctly(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, self.trip.origin)
        self.assertContains(self.response, self.trip.destination)
        self.assertNotContains(self.response, "Hi I should not be on this page")

    def test_trip_detail_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripDetailView.as_view().__name__)

    def test_anonymous_user_can_access_trip_detail_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

    def test_logged_in_user_can_access_trip_detail_view(self):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)


class TripCreateViewTests(TestCase):
    """Test suite for the trip create view"""

    def setUp(self):
        self.owner = CompanyOwnerFactory()
        self.company = CompanyFactory(owner=self.owner)
        self.login_url = reverse_lazy("account_login")
        self.url = reverse_lazy("companies:trip_create", args=[str(self.company.slug)])
        self.template_name = "trips/trip_form.html"
        self.permission = "trips.add_trip"

    def test_company_trip_create_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripCreateView.as_view().__name__)

    def test_company_trip_create_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_create_view_is_not_accessible_by_logged_in_normal_public_user(
        self,
    ):
        user = UserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_create_view_is_not_accessible_by_staffuser(self):
        user = StaffuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff but not superuser and correctly authenticated
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert staff user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_create_view_is_accessible_by_superuser(self):
        user = SuperuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff | superuser and correctly authenticated
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Create")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_trip_create_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the trip create page."""

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Create")
        self.assertNotContains(response, "Hi I should not be on this page!")
