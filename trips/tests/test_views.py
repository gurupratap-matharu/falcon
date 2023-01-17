from http import HTTPStatus

from django.test import TestCase
from django.urls import resolve, reverse

from trips.views import TripListView


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
