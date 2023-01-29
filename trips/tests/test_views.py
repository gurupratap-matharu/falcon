from http import HTTPStatus

from django.test import TestCase
from django.urls import resolve, reverse

from trips.factories import TripFactory
from trips.views import TripDetailView, TripListView
from users.factories import UserFactory


class TripListViewTests(TestCase):
    """
    Test suite for trip list view.
    """

    def setUp(self):
        self.url = reverse("trips:trip-list")
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
