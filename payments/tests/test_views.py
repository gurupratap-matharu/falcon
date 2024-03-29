from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from orders.factories import OrderFactory
from payments.views import (
    PaymentFailView,
    PaymentPendingView,
    PaymentSuccessView,
    PaymentView,
    mercadopago_success,
)


class PaymentViewTests(TestCase):
    """
    Test suite for the main payment view which shows all payments options and initializes
    mercado pago sdk.
    """

    def setUp(self):
        self.url = reverse("payments:home")
        self.template_name = "payments/payment.html"

    def test_payment_home_page_works_for_valid_order_in_session(self):
        # create an order and set it in the session as payment view expects it
        self.order = OrderFactory(paid=False)
        session = self.client.session
        session["order"] = str(self.order.id)  # type:ignore
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Payment")
        self.assertNotContains(response, "Hi there! I should not be on this page.")
        self.assertContains(response, "mp_public_key")
        self.assertContains(response, "preference")
        self.assertContains(response, "order")
        self.assertEqual(response.context["order"], self.order)

    def test_payment_home_page_redirect_to_home_if_order_not_found_in_session(self):
        # create an order but DO NOT set it in the session
        self.order = OrderFactory(paid=False)

        response = self.client.get(self.url)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("pages:home"), HTTPStatus.FOUND)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PaymentView.redirect_message)

        self.assertTemplateNotUsed(response, self.template_name)

    def test_payment_home_page_url_resolves_payment_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentView.as_view().__name__)


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
        self.assertContains(self.response, "Kpiola")

    def test_payment_success_page_does_not_contain_incorrect_html(self):
        self.assertNotContains(self.response, "Hi there! I should not be on this page.")

    def test_payment_success_page_url_resolves_payment_success_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentSuccessView.as_view().__name__)


class PaymentPendingViewTests(SimpleTestCase):
    """Test suite for payment pending view"""

    def setUp(self):
        self.url = reverse("payments:pending")
        self.response = self.client.get(self.url)
        self.template_name = "payments/payment_pending.html"

    def test_payment_pending_page_status_code(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)

    def test_payment_pending_page_renders_correct_template(self):
        self.assertTemplateUsed(self.response, self.template_name)

    def test_payment_pending_page_contains_correct_html(self):
        self.assertContains(self.response, "Pending")

    def test_payment_pending_page_does_not_contain_incorrect_html(self):
        self.assertNotContains(self.response, "Hi there! I should not be on this page.")

    def test_payment_pending_page_url_resolves_payment_pending_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentPendingView.as_view().__name__)


class PaymentFailViewTests(SimpleTestCase):
    """Test suite for payment fail view"""

    def setUp(self):
        self.url = reverse("payments:fail")
        self.response = self.client.get(self.url)
        self.template_name = "payments/payment_fail.html"

    def test_payment_fail_page_status_code(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)

    def test_payment_fail_page_renders_correct_template(self):
        self.assertTemplateUsed(self.response, self.template_name)

    def test_payment_fail_page_contains_correct_html(self):
        self.assertContains(self.response, "Unsuccessful")

    def test_payment_fail_page_does_not_contain_incorrect_html(self):
        self.assertNotContains(self.response, "Hi there! I should not be on this page.")

    def test_payment_fail_page_url_resolves_payment_fail_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentFailView.as_view().__name__)


class CheckoutViewTests(TestCase):
    """Test suite for stripe checkout view"""

    def setUp(self):
        self.url = reverse("payments:checkout")

    def test_checkout_page_is_not_accessible_via_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)
