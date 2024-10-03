import pdb
import uuid
from http import HTTPStatus
from unittest.mock import patch

from django.conf import settings
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client, SimpleTestCase, TestCase
from django.urls import resolve, reverse
from django.utils import translation

from orders.factories import OrderFactory, OrderItemFactory, PassengerFactory
from payments.models import ModoToken, WebhookMessage
from payments.views import (
    ModoView,
    PaymentCancelView,
    PaymentFailView,
    PaymentPendingView,
    PaymentSuccessView,
    PaymentView,
    mercadopago_success,
)
from trips.factories import SeatFactory, TripPastFactory
from trips.models import Seat

from .utils import ModoMock


class PaymentViewTests(TestCase):
    """
    Test suite for the main payment view which shows all payments options and initializes
    mercado pago sdk.
    """

    def setUp(self):
        self.url = reverse("payments:home")
        self.template_name = "payments/payment.html"
        self.order = OrderFactory(paid=False)
        self.order_item = OrderItemFactory(order=self.order)

        session = self.client.session
        session["order"] = str(self.order.id)
        session.save()

    def test_payment_home_page_url_resolves_payment_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentView.as_view().__name__)

    def test_payment_view_only_accepts_get_request(self):

        response = self.client.post(self.url)  # try POST
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_payment_home_page_redirect_to_home_if_order_not_found_in_session(self):
        # clear the order in session that we added in setup
        session = self.client.session
        session.clear()
        session.save()

        response = self.client.get(self.url, follow=True)

        messages = list(get_messages(response.wsgi_request))

        self.assertRedirects(response, reverse("pages:home"), HTTPStatus.FOUND)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTemplateUsed(response, "pages/home.html")
        self.assertTemplateNotUsed(response, self.template_name)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), PaymentView.redirect_message)

    def test_payment_home_page_works_for_valid_order_in_session(self):

        # Arrange
        # order already set in session in setup method

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

        self.assertContains(response, "Payment")
        self.assertContains(response, "mp_public_key")
        self.assertContains(response, "preference")

        self.assertNotContains(response, "Hi there! I should not be on this page.")

        self.assertEqual(response.context["order"], self.order)
        self.assertEqual(response.context["mp_public_key"], settings.MP_PUBLIC_KEY)


class MercadoPagoSuccessView(TestCase):
    """Test suite for mercado pago payment success view"""

    def setUp(self):
        self.url = reverse("payments:mercadopago_success")

        size = 2  # num of passengers

        SeatFactory.reset_sequence(1)
        self.trip = TripPastFactory()
        self.seats = SeatFactory.create_batch(
            size=size, trip=self.trip, seat_status=Seat.AVAILABLE
        )

        self.passengers = PassengerFactory.create_batch(size=size)
        self.order = OrderFactory(paid=False, passengers=self.passengers)
        self.order_item = OrderItemFactory(
            order=self.order, trip=self.trip, quantity=size, seats="1, 2"
        )

        session = self.client.session
        session["order"] = str(self.order.id)
        session.save()

    def test_redirect_for_successful_payment(self):
        # Arrange
        # MP response for a successful payment
        data = {
            "collection_id": 54650347595,
            "collection_status": "approved",
            "payment_id": 54650347595,
            "status": "approved",
            "external_reference": str(self.order.id),
            "payment_type": "account_money",
            "merchant_order_id": "7712864656",
            "preference_id": "1272408260-35ff1ef7-3eb8-4410-b219-4a98ef386ac0",
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }

        # Act
        response = self.client.get(self.url, data=data)

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("payments:success"), HTTPStatus.FOUND)

    def test_redirect_to_failure_page_for_unsuccessful_payment(self):
        # Arrange
        data = {
            "collection_id": 54650347595,
            "collection_status": "rejected",
            "payment_id": 54650347595,
            "status": "rejected",  # <-- unsuccessful payment
            "external_reference": str(self.order.id),
            "payment_type": "credit_card",
            "merchant_order_id": "7712864656",
            "preference_id": "1272408260-35ff1ef7-3eb8-4410-b219-4a98ef386ac0",
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }

        # Act
        response = self.client.get(self.url, data=data)

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("payments:fail"), HTTPStatus.FOUND)

    def test_mercadopago_payment_success_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, mercadopago_success.__name__)

    def test_confirms_order_upon_successful_payment(self):
        # this is a like an integration test for mercadopago

        # first make sure that our order is unpaid, w/o payment_id, w/o passengers

        self.assertFalse(self.order.paid)
        self.assertEqual(self.order.payment_id, "")

        self.assertTrue(self.seats[0].seat_status, Seat.AVAILABLE)
        self.assertTrue(self.seats[1].seat_status, Seat.AVAILABLE)

        self.assertIsNone(self.seats[0].passenger)
        self.assertIsNone(self.seats[1].passenger)

        self.assertFalse(WebhookMessage.objects.exists())

        # Arrange
        PAYMENT_ID = "54650347595"
        data = {
            "collection_id": PAYMENT_ID,
            "collection_status": "approved",
            "payment_id": PAYMENT_ID,
            "status": "approved",
            "external_reference": str(self.order.id),
            "payment_type": "account_money",
            "merchant_order_id": "7712864656",
            "preference_id": str(uuid.uuid4()),
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }

        # Act
        response = self.client.get(self.url, data=data, follow=True)

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse("payments:success"), HTTPStatus.FOUND)
        self.assertTemplateUsed(response, PaymentSuccessView.template_name)

        self.order.refresh_from_db()
        self.seats[0].refresh_from_db()
        self.seats[1].refresh_from_db()

        # now make sure order got paid with the same payment id attached to it

        self.assertTrue(self.order.paid)
        self.assertEqual(self.order.payment_id, PAYMENT_ID)

        # make sure the seats are in booked status with passengers assigned to them

        self.assertTrue(self.seats[0].seat_status, Seat.BOOKED)
        self.assertTrue(self.seats[1].seat_status, Seat.BOOKED)

        self.assertIn(self.seats[0].passenger, self.passengers)
        self.assertIn(self.seats[1].passenger, self.passengers)

        # lastly make sure emails are sent
        self.assertEqual(len(mail.outbox), 2)

        # make sure webhook data is saved to db
        self.assertTrue(WebhookMessage.objects.exists())
        webhook_message = WebhookMessage.objects.first()

        self.assertEqual(webhook_message.provider, WebhookMessage.MERCADOPAGO)
        self.assertEqual(webhook_message.payload, data)

    def test_does_not_confirm_order_upon_failed_payment(self):

        self.assertFalse(self.order.paid)
        self.assertEqual(self.order.payment_id, "")

        self.assertEqual(self.seats[0].seat_status, Seat.AVAILABLE)
        self.assertEqual(self.seats[1].seat_status, Seat.AVAILABLE)

        self.assertIsNone(self.seats[0].passenger)
        self.assertIsNone(self.seats[1].passenger)

        self.assertFalse(WebhookMessage.objects.exists())

        # Arrange
        payment_id = "54650347595"
        data = {
            "collection_id": payment_id,
            "collection_status": "rejected",  # <-- we pass rejected and not approved
            "payment_id": payment_id,
            "status": "rejected",  # <-- we pass rejected and not approved
            "external_reference": str(self.order.id),
            "payment_type": "account_money",
            "merchant_order_id": "7712864656",
            "preference_id": str(uuid.uuid4()),
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }

        # Act
        response = self.client.get(self.url, data=data, follow=True)

        # Assert

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse("payments:fail"), HTTPStatus.FOUND)
        self.assertTemplateUsed(response, PaymentFailView.template_name)

        # assert order
        self.order.refresh_from_db()
        self.assertFalse(self.order.paid)
        self.assertEqual(self.order.payment_id, "")

        # assert seats
        self.assertEqual(self.seats[0].seat_status, Seat.AVAILABLE)
        self.assertEqual(self.seats[1].seat_status, Seat.AVAILABLE)

        self.assertIsNone(self.seats[0].passenger)
        self.assertIsNone(self.seats[1].passenger)

        # assert webhook
        msg = WebhookMessage.objects.first()

        self.assertTrue(WebhookMessage.objects.exists())
        self.assertEqual(msg.provider, WebhookMessage.MERCADOPAGO)
        self.assertEqual(msg.payload, data)


class PaymentSuccessViewTests(TestCase):
    """Test suite for payment success view"""

    def setUp(self):
        self.url = reverse("payments:success")
        self.template_name = PaymentSuccessView.template_name

        # create a paid order and set it in the session as payment success view expects it
        self.order = OrderFactory(paid=True)
        self.order_item = OrderItemFactory(order=self.order)
        session = self.client.session
        session["order"] = str(self.order.id)
        session.save()

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)

    def test_payment_success_page_url_resolves_payment_success_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentSuccessView.as_view().__name__)

    def test_payment_success_view_only_accepts_get_request(self):
        response = self.client.post(self.url)  # try POST
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_payment_success_view_works_correctly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

        self.assertContains(response, "Payment Successful!")
        self.assertContains(response, "Tickets Booked!")
        self.assertContains(response, "Book Return Ticket")
        self.assertContains(response, "Add to calendar")
        self.assertContains(response, "Download")
        self.assertContains(response, self.order.email)

        self.assertNotContains(response, "Hi there! I should not be on this page.")

        self.assertIn("order", response.context)
        self.assertEqual(response.context["order"], self.order)

    def test_payment_success_spanish_render(self):
        response = self.client.get(self.url, headers={"accept-language": "es"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

        self.assertContains(response, "Pago exitoso!")
        self.assertContains(response, "Pasajes reservados!")
        self.assertContains(response, "Reservar otro pasaje")
        self.assertContains(response, "Añadir al calendario")
        self.assertContains(response, "Descargar")
        self.assertContains(response, self.order.email)

        self.assertNotContains(response, "Hi there! I should not be on this page.")

        self.assertIn("order", response.context)
        self.assertEqual(response.context["order"], self.order)

    def test_payment_success_portuguese_render(self):
        response = self.client.get(self.url, headers={"accept-language": "pt"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

        self.assertContains(response, "Pagamento exitoso!")
        self.assertContains(response, "Ingressos reservados!")
        self.assertContains(response, "Reservar outro ingresso")
        self.assertContains(response, "Adicionar ao calendário")
        self.assertContains(response, "Baixar")
        self.assertContains(response, self.order.email)

        self.assertNotContains(response, "Hi there! I should not be on this page.")

        self.assertIn("order", response.context)
        self.assertEqual(response.context["order"], self.order)

    def test_order_is_removed_from_session_in_payment_success_view(self):
        """
        If order is kept in session for say 10 mins it should not be a problem.
        Suppose the user immediately goes to buy a return ticket then the order in
        session should be replaced.

        Although we should test this full process of booking two tickets consecutively
        or with delay.

        For now skipping this test because if we immediately remove the order then
        a page refresh on payment success throws 404. Not sure if its desirable.
        """

        self.skipTest("Test completed but yet to decide")
        # Initially order should be in session as we put it in setup()

        self.assertIn("order", self.client.session)
        self.assertEqual(self.client.session["order"], str(self.order.id))

        # We now access the view and it should remove order from the session
        _ = self.client.get(self.url)

        self.assertNotIn("order", self.client.session)
        with self.assertRaises(KeyError):
            self.client.session["order"]


class PaymentCancelViewTests(SimpleTestCase):
    """Test suite for payment cancel view"""

    def setUp(self):
        self.url = reverse("payments:cancel")
        self.template_name = PaymentCancelView.template_name

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)

    def test_payment_cancel_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentCancelView.as_view().__name__)

    def test_accepts_only_get_request(self):
        response = self.client.post(self.url)  # try post
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_payment_cancel_view_works_correctly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Payment Cancel")
        self.assertContains(response, "contact us here")
        self.assertContains(response, "Go back home")
        self.assertNotContains(response, "Hi there! I should not be on this page.")

    def test_spanish_render(self):
        response = self.client.get(self.url, headers={"accept-language": "es"})

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pago cancelado")
        self.assertContains(response, "escribirnos aquí")
        self.assertContains(response, "Volver a home")
        self.assertNotContains(response, "Hi there! I should not be on this page.")

    def test_portuguese_render(self):
        response = self.client.get(self.url, headers={"accept-language": "pt"})

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pagamento cancelado")
        self.assertContains(response, "entre em contato conosco aqui")
        self.assertContains(response, "Volto para home")
        self.assertNotContains(response, "Hi there! I should not be on this page.")


class PaymentPendingViewTests(SimpleTestCase):
    """Test suite for payment pending view"""

    def setUp(self):
        self.url = reverse("payments:pending")
        self.template_name = PaymentPendingView.template_name

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)

    def test_payment_pending_page_url_resolves_payment_pending_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentPendingView.as_view().__name__)

    def test_accepts_only_get_request(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_payment_pending_view_works_correctly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Payment Pending")
        self.assertContains(response, "contact us here")
        self.assertContains(response, "Go back home")
        self.assertNotContains(response, "Hi there! I should not be on this page.")

    def test_spanish_render(self):
        response = self.client.get(self.url, headers={"accept-language": "es"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pago pendiente")
        self.assertContains(response, "escribirnos aquí")
        self.assertContains(response, "Volver a home")
        self.assertNotContains(response, "Hi there! I should not be on this page.")

    def test_portuguese_render(self):
        response = self.client.get(self.url, headers={"accept-language": "pt"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pagamento pendente")
        self.assertContains(response, "entre em contato conosco aqui")
        self.assertContains(response, "Volto para home")
        self.assertNotContains(response, "Hi there! I should not be on this page.")


class PaymentFailViewTests(SimpleTestCase):
    """Test suite for payment fail view"""

    def setUp(self):
        self.url = reverse("payments:fail")
        self.template_name = PaymentFailView.template_name

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)

    def test_payment_fail_page_url_resolves_payment_fail_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, PaymentFailView.as_view().__name__)

    def test_payment_fail_view_only_accepts_get_request(self):
        response = self.client.post(self.url)  # try POST
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_payment_fail_page_works_correctly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Payment Unsuccessful")
        self.assertContains(response, "Go back home")
        self.assertContains(response, "Try again")
        self.assertContains(response, "contact us here")
        self.assertNotContains(response, "Hi there! I should not be on this page.")

    def test_spanish_language_render(self):
        response = self.client.get(self.url, headers={"accept-language": "es"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pago no fue procesado")
        self.assertContains(response, "Volver a home")
        self.assertContains(response, "Probar de nuevo")
        self.assertContains(response, "escribirnos aquí")
        self.assertNotContains(response, "Hi there! I should not be on this page.")

    def test_portuguese_language_render(self):
        response = self.client.get(self.url, headers={"accept-language": "pt"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pagamento sem sucesso")
        self.assertContains(response, "Volto para home")
        self.assertContains(response, "Tente novamente")
        self.assertContains(response, "entre em contato conosco aqui")
        self.assertNotContains(response, "Hi there! I should not be on this page.")


class CheckoutViewTests(TestCase):
    """Test suite for stripe checkout view"""

    def setUp(self):
        self.url = reverse("payments:checkout")

    def test_checkout_page_is_not_accessible_via_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)


@patch("payments.views.create_payment_intent", ModoMock)
class ModoViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ModoToken.objects.create(token=uuid.uuid4())

    def setUp(self):
        self.url = reverse("payments:modo")
        self.template_name = ModoView.template_name
        self.order = OrderFactory(paid=False)
        self.order_item = OrderItemFactory(order=self.order)

        session = self.client.session
        session["order"] = str(self.order.id)
        session.save()

    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)

    def test_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, ModoView.as_view().__name__)

    def test_accepts_only_get_request(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_renders_correctly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Pay with Modo")
        self.assertNotContains(response, "Hi I should not be on this page")

        self.assertEqual(response.context["order"], self.order)
        self.assertContains(response, "payment_intent")


class MercadoPagoWebhookTests(TestCase):
    """
    Test suite to check the integrity of Mercado Pago webhook endpoint.
    """

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse("payments:mercadopago-webhook")

    def test_webhook_does_not_accept_get_method(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_missing_token(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(
            response.content.decode(), "Incorrect token in MP webhook header."
        )
