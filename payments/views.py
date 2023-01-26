import logging
import secrets
from http import HTTPStatus
from typing import Any, Dict

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

import mercadopago
import stripe

logger = logging.getLogger(__name__)

mercado_pago = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentView(TemplateView):
    """A simple view that shows all payment options for our project"""

    template_name: str = "payments/payment.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.GET:
            self.request.session["order"] = self.request.GET
            logger.info("Veer storing order data in session: %s " % self.request.GET)

        current_site = get_current_site(self.request)

        back_url_success = "http://%s%s" % (
            current_site.domain,
            reverse_lazy("payments:success"),
        )
        back_url_failure = "http://%s%s" % (
            current_site.domain,
            reverse_lazy("payments:fail"),
        )

        picture_url = "http://%s%s" % (
            current_site.domain,
            static("assets/img/bus/bus4.jpg"),
        )

        logger.info("Veer back_url_success: %s", back_url_success)
        logger.info("Veer back_url_failure: %s", back_url_failure)
        logger.info("Veer picture_url: %s", picture_url)

        # Create mercado page preference
        preference_data = {
            "items": [
                {
                    "id": "Trip-id-1234",
                    "title": "My Bus ticket",
                    "currency_id": "ARS",
                    "quantity": 1,
                    "picture_url": picture_url,
                    "description": "BUE - MZA Cama Tommorow Night",
                    "category_id": "Andesmar",
                    "unit_price": 1.23,
                }
            ],
            "payer": {
                "name": "Juan",
                "surname": "Lopez",
                "email": "juan.lopez@email.com",
                "phone": {"area_code": "11", "number": "4444-4444"},
                "identification": {"type": "DNI", "number": "12345678"},
                "address": {
                    "street_name": "Street",
                    "street_number": 123,
                    "zip_code": "5700",
                },
            },
            "back_urls": {
                "success": back_url_success,
                "failure": back_url_failure,
                "pending": "",
            },
            "auto_return": "approved",
            "notification_url": "https://webhook.site/a40b5b6a-26a9-4261-9a2c-1b9b7fa9fb85",  # temporary webhook
            "statement_descriptor": "Falcon",
            "external_reference": "Reference_1234",
            "binary_mode": True,
        }

        logger.info("veer mercado pago preference_data: %s", preference_data)

        preference_response = mercado_pago.preference().create(preference_data)

        context["preference"] = preference_response["response"]
        context["mp_public_key"] = settings.MP_PUBLIC_KEY
        return context


class CheckoutView(TemplateView):
    template_name: str = "pages/checkout.html"

    def post(self, request, *args, **kwargs):
        current_site = get_current_site(self.request)
        success_url = "http://%s%s" % (
            current_site.domain,
            reverse_lazy("payments:success"),
        )
        cancel_url = "http://%s%s" % (
            current_site.domain,
            reverse_lazy("payments:fail"),
        )

        amount = secrets.randbelow(1000)

        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email="customer@example.com",
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Bus Ticket",
                            },
                            "unit_amount": amount,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception as e:
            return str(e)

        return redirect(checkout_session.url, code=303)


class PaymentSuccessView(TemplateView):
    template_name: str = "payments/payment_success.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        logger.info("veer mercado pago says %s" % self.request.GET)

        return super().get_context_data(**kwargs)


class PaymentFailView(TemplateView):
    template_name: str = "payments/payment_fail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        logger.info("veer mercado pago says %s" % self.request.GET)

        return super().get_context_data(**kwargs)


class PaymentCancelView(TemplateView):
    template_name: str = "payments/payment_cancel.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        logger.info("veer mercado pago says %s" % self.request.GET)

        return super().get_context_data(**kwargs)


@csrf_exempt
def stripe_webhook(request):
    """
    Our internal webhook registered with stripe which listens for payment
    notifications.

    A confirmation on this hook is a guarantee that the payment is successful.
    # TODO: May be store the confirmation data in a model or email
    """

    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = settings.STRIPE_WEBHOOK_SIGNING_SECRET
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    logger.info(
        "veer inside stripe webhook: payload: %s, sig_header: %s", payload, sig_header
    )

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    except ValueError as e:
        # Invalid payload
        logger.warning("Invalid payload received in stripe webhook: %s", e)
        return HttpResponseBadRequest()

    except stripe.error.SignatureVerificationError as e:  # type: ignore
        # Invalid signature
        logger.warning("Invalid signature received in stripe webhook: %s", e)

        return HttpResponseBadRequest()

    logger.info("veer following event received: %s", event)

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        logger.info("Stripe: Payment was successful!!! :D")
        # TODO: run some custom code here
        # Saving a copy of the order in your own database.
        # Sending the customer a receipt email.

    return HttpResponse(status=HTTPStatus.OK)
