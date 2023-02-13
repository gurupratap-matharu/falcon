import pdb
from http import HTTPStatus

from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from orders.factories import OrderFactory
from payments.views import PaymentSuccessView, mercadopago_success


class MercadoPagoSuccessView(TestCase):
    """Test suite for mercado pago payment success view"""

    def setUp(self):
        self.url = reverse("payments:mercadopago_success")

    def test_mercadopago_payment_success_view_redirects_correctly(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("payments:success"), HTTPStatus.FOUND)

    def test_mercadopago_payment_success_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, mercadopago_success.__name__)

    def test_mercadopago_payment_success_view_confirms_order_with_correct_query_params(
        self,
    ):
        order = OrderFactory(paid=False)
        self.assertFalse(order.paid)
        data = {
            "collection_id": 54650347595,
            "collection_status": "approved",
            "payment_id": 54650347595,
            "status": "approved",
            "external_reference": str(order.id),
            "payment_type": "account_money",
            "merchant_order_id": "7712864656",
            "preference_id": "1272408260-35ff1ef7-3eb8-4410-b219-4a98ef386ac0",
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }
        response = self.client.get(self.url, data=data)

        order.refresh_from_db()

        self.assertRedirects(response, reverse("payments:success"), HTTPStatus.FOUND)
        self.assertTrue(order.paid)

    def test_mercadopago_payment_success_view_does_not_confirm_order_with_incorrect_query_params(
        self,
    ):
        # basically we set the status not equal to approved but yet have correct order id
        order = OrderFactory(paid=False)
        self.assertFalse(order.paid)
        data = {
            "collection_id": 54650347595,
            "collection_status": "rejected",  # <-- we pass rejected and not approved
            "payment_id": 54650347595,
            "status": "rejected",  # <-- we pass rejected and not approved
            "external_reference": str(order.id),  # type:ignore
            "payment_type": "account_money",
            "merchant_order_id": "7712864656",
            "preference_id": "1272408260-35ff1ef7-3eb8-4410-b219-4a98ef386ac0",
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }
        response = self.client.get(self.url, data=data)

        order.refresh_from_db()  # type:ignore

        self.assertRedirects(response, reverse("payments:success"), HTTPStatus.FOUND)
        self.assertFalse(order.paid)  # <-- order should not be paid


class PaymentSuccessViewTests(SimpleTestCase):
    """Test suite for payment success view"""

    def setUp(self):
        self.url = reverse("payments:success")
        self.response = self.client.get(self.url)
        self.template_name = "payments/payment_success.html"

    def test_payment_success_page_status_code(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)

    def test_payment_success_page_template(self):
        self.assertTemplateUsed(self.response, self.template_name)

    def test_payment_success_page_contains_correct_html(self):
        self.assertContains(self.response, "success")
        self.assertContains(self.response, "Falcon")

    def test_payment_success_page_does_not_contain_incorrect_html(self):
        self.assertNotContains(self.response, "Hi there! I should not be on this page.")

    def test_payment_success_page_url_resolves_homepageview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentSuccessView.as_view().__name__)
