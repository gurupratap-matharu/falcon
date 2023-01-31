from http import HTTPStatus

from django.test import TestCase
from django.urls import resolve, reverse_lazy

from orders.views import OrderCreateView, OrderView


class OrderPageTests(TestCase):
    """
    Test suite for order view.

    # VEER YOU MIGHT WANT TO REMOVE THIS TEST SUITE
    """

    def setUp(self):
        self.url = reverse_lazy("orders:home")
        self.template_name = "orders/order.html"
        self.response = self.client.get(self.url)

    def test_order_page_status_code(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)

    def test_order_page_template(self):
        self.assertTemplateUsed(self.response, self.template_name)

    def test_order_page_html(self):
        self.assertContains(self.response, "Order")
        self.assertNotContains(self.response, "Hi I should not be on this page")

    def test_order_url_resolves_orderview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, OrderView.as_view().__name__)

    def test_order_page_renders_order_form(self):
        # TODO: Veer implemente this
        pass

    def test_order_page_renders_correct_number_of_passenger_forms(self):
        # TODO: Veer implemente this
        pass

    def test_order_creation_for_valid_post_data(self):
        # TODO: Veer implemente this
        pass

    def test_order_validation_errors_for_invalid_post_data(self):
        # TODO: Veer implemente this
        pass

    def test_order_creation_shows_message_on_successful_creation(self):
        # TODO: Veer implemente this
        pass


class OrderCreateViewTests(TestCase):
    """
    Test suite for order create view.
    """

    def setUp(self):
        self.url = reverse_lazy("orders:create")
        self.template_name = "orders/order_form.html"

    def test_order_create_view_works(self):
        self.response = self.client.get(self.url)

        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, "Order")
        self.assertNotContains(self.response, "Hi I should not be on this page")

    def test_order_create_url_resolves_ordercreateview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, OrderCreateView.as_view().__name__)
