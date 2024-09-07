"""
Since here we are testing the main home page of our site we move it
to an independent script as this might get larger in the future.
"""

from http import HTTPStatus

from django.test import SimpleTestCase, tag
from django.urls import resolve, reverse

from pages.views import HomePageView


@tag("pages", "fast")
class HomePageTests(SimpleTestCase):
    """
    Test suite for the main home page or our awesome site.
    """

    def setUp(self):
        self.url = reverse("pages:home")
        self.response = self.client.get(self.url)
        self.template_name = "pages/home.html"

    def test_homepage_works(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, "Ventanita")
        self.assertNotContains(self.response, "Hi there! I should not be on this page.")

    def test_homepage_url_resolves_homepageview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, HomePageView.as_view().__name__)
