from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from companies.factories import CompanyFactory
from trips.factories import (
    LocationFactory,
    TripFactory,
    TripPastFactory,
    TripTomorrowFactory,
)
from trips.models import Trip
from trips.views import (
    CompanyTripListView,
    TripCreateView,
    TripDetailView,
    TripListView,
)
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
        self.url = reverse_lazy("companies:trip-create", args=[str(self.company.slug)])
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

    def test_trip_create_view_works_on_successful_post(self):
        """
        This is an end-to-end kind of test for trip creation.
        """

        # Create two locations as trip needs their ids since they are foreign keys
        origin, destination = LocationFactory.create_batch(size=2)
        # Build data
        data = {
            "name": "Europe Trip",
            "origin": str(origin.id),
            "destination": str(destination.id),
            "departure": "2023-03-16 15:00",
            "arrival": "2023-03-31 16:00",
            "price": "1",
            "status": "A",
            "mode": "D",
            "image": "",
            "description": "",
        }

        self.client.force_login(self.owner)  # type:ignore

        # Creation will redirect to trip-detail so make `follow=True`
        response = self.client.post(path=self.url, data=data, follow=True)

        # Get trip created in DB
        trip = Trip.objects.first()
        expected_url = trip.get_absolute_url()

        # Verify redirection
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        # Verify DB count and content
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(trip.name, "Europe Trip")
        self.assertEqual(trip.slug, "europe-trip")
        self.assertEqual(trip.origin, origin)
        self.assertEqual(trip.destination, destination)
        self.assertEqual(trip.status, "A")
        self.assertEqual(trip.mode, "D")

        # Verify content of final redirected page
        self.assertContains(response, trip.name)
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Verify trip creation success message on final page.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), TripCreateView.success_message)


class CompanyTripListViewTests(TestCase):
    """Test suite for company trip list view"""

    def setUp(self):
        self.owner = CompanyOwnerFactory()
        self.company = CompanyFactory(owner=self.owner)
        self.trips = TripTomorrowFactory.create_batch(
            size=2, company=self.company, status=Trip.ACTIVE
        )
        self.inactive_trip = TripPastFactory(company=self.company)

        self.url = self.company.get_trip_list_url()  # type:ignore
        self.template_name = "trips/company_trip_list.html"
        self.permission = "trips.view_trip"
        self.login_url = reverse_lazy("account_login")

    def test_company_trip_list_resolves_correct_view(self):
        view = resolve(self.url)

        self.assertEqual(view.func.__name__, CompanyTripListView.as_view().__name__)

    def test_company_trip_list_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_list_view_is_not_accessible_by_logged_in_normal_public_user(
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

    def test_company_trip_list_view_is_not_accessible_by_staffuser(self):
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

    def test_company_trip__view_is_accessible_by_superuser(self):
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
        self.assertContains(response, "Upcoming Trips")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_trip_list_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the trip list page."""

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
        self.assertContains(response, "Upcoming Trips")
        self.assertContains(response, "Create Trip")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert valid trips are shown
        trips = response.context["trips"]
        self.assertEqual(len(trips), 2)
        self.assertIn(self.trips[0], trips)
        self.assertIn(self.trips[1], trips)
        self.assertNotIn(self.inactive_trip, trips)

        # Assert company itself in context
        self.assertEqual(self.company, response.context["company"])
