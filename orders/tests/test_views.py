from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from orders.forms import OrderForm, PassengerForm
from orders.views import OrderCreateView


class OrderCreateTests(TestCase):
    """
    Test suite for the main and very complex order create view
    """

    search_query = {
        "trip_type": "round_trip",
        "num_of_passengers": "2",
        "origin": "Alta Gracia",
        "destination": "Anatuya",
        "departure": "23-02-2023",
        "return": "",
    }

    def setUp(self):
        self.url = reverse_lazy("orders:order_create")
        self.template_name = "orders/order_form.html"
        session = self.client.session
        session["q"] = self.search_query
        session.save()

    # GET
    def test_order_create_page_works_via_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "orders/order_form.html")
        self.assertContains(response, "Order")
        self.assertContains(response, "Passenger")
        self.assertIn("cart", response.context)
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_order_create_url_resolves_ordercreateview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, OrderCreateView.as_view().__name__)

    def test_order_page_renders_order_form(self):
        response = self.client.get(self.url)
        self.assertIn("form", response.context)
        self.assertIn("formset", response.context)
        self.assertIsInstance(response.context["form"], OrderForm)

    def test_order_page_renders_passenger_formset_correctly(self):
        response = self.client.get(self.url)
        formset = response.context["formset"]

        self.assertIn("formset", response.context)
        self.assertIsInstance(formset.forms[0], PassengerForm)
        self.assertEqual(formset.total_form_count(), 2)

    def test_order_page_redirects_to_home_if_no_query_found_in_session(self):
        # first let's clear the session set in setup()
        session = self.client.session
        session.clear()
        session.save()

        # now hit the order create page directly
        response = self.client.get(self.url)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse_lazy("pages:home"), HTTPStatus.FOUND)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), OrderCreateView.redirect_message)

    # POST

    def test_order_creation_for_valid_post_data(self):
        # TODO: Veer implemente this
        pass

    def test_order_validation_errors_for_invalid_post_data(self):
        # TODO: Veer implemente this
        pass

    def test_order_creation_shows_message_on_successful_creation(self):
        # TODO: Veer implemente this
        pass
