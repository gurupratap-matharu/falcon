import logging
from http import HTTPStatus
from typing import Any, Dict

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

import mercadopago
import stripe

from orders.models import Order

logger = logging.getLogger(__name__)

mercado_pago = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentView(TemplateView):
    """A simple view that shows all payment options for our project"""

    template_name: str = "payments/payment.html"
    order = None

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["order"] = self.order = get_object_or_404(
            Order, id=self.request.session["order"]
        )
        context["preference"] = self.get_mercado_pago_preference()
        context["mp_public_key"] = settings.MP_PUBLIC_KEY

        logger.info("veer retrieved order(👩🏻‍⚖️) from session as: %s", self.order)

        return context

    def build_abs_url(self, url=None):
        current_site = get_current_site(self.request)
        return "http://%s%s" % (current_site.domain, url)

    def get_mercado_pago_preference(self):
        """Get reponse from Mercado Pago for preference (item) data."""

        order = self.order
        unit_price = float(order.get_total_cost() / 1000)  # <-- Minimizing this for MP

        picture_url = self.build_abs_url(url=static("assets/img/bus/bus4.jpg"))
        success = self.build_abs_url(url=reverse_lazy("payments:success"))
        failure = self.build_abs_url(url=reverse_lazy("payments:fail"))
        pending = self.build_abs_url(url=reverse_lazy("payments:pending"))
        notification_url = self.build_abs_url(
            url=reverse_lazy("payments:mercadopago_webhook")
        )

        logger.info("mercado pago success: %s", success)
        logger.info("mercado pago failure: %s", failure)
        logger.info("mercado pago pending: %s", pending)
        logger.info("mercado pago picture_url: %s", picture_url)
        logger.info("mercado pago notification_url: %s", notification_url)

        # Create mercado page preference
        # veer we use quantity as always 1 with full order price 😉
        preference_data = {
            "items": [
                {
                    "id": str(order.id),
                    "title": "My Bus ticket",  # <-- could be customized
                    "currency_id": "ARS",
                    "picture_url": picture_url,
                    "description": "Bus Ticket",  # <-- could be customized
                    "category_id": "Bus Ticket",
                    "quantity": 1,
                    "unit_price": unit_price,
                }
            ],
            # "payer": {
            #     "name": order.name,
            #     "surname": "",
            #     "email": order.email,
            #     "phone": {"area_code": "11", "number": "4444-4444"},
            #     "identification": {"type": "DNI", "number": "12345678"},
            #     "address": {
            #         "street_name": "Uspallata",
            #         "street_number": 471,
            #         "zip_code": "1096",
            #     },
            # },
            "back_urls": {
                "success": success,
                "failure": failure,
                "pending": pending,
            },
            "auto_return": "approved",
            "notification_url": notification_url,
            "statement_descriptor": "FalconHunt",
            "external_reference": str(order.id),
            "binary_mode": True,
        }

        logger.info("veer mercado pago preference_data: %s", preference_data)

        preference = mercado_pago.preference().create(preference_data)

        logger.info("veer mercado pago preference response(💰): %s", preference)

        return preference["response"]


class CheckoutView(TemplateView):
    """
    Stripe checkout view

    This view actually doesn't render any template. It just receives post data
    from payment options page and creates a checkout session and redirects to it.

    The user is routed back to our site based on the payment status.
    """

    template_name: str = "payments/checkout.html"  # <-- veer this is dummy

    def build_abs_url(self, url=None):
        current_site = get_current_site(self.request)
        return "http://%s%s" % (current_site.domain, url)

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, id=self.request.session["order"])
        client_reference_id = str(order.id)
        amount = int(order.get_total_cost_usd() * 100)
        success_url = self.build_abs_url(url=reverse_lazy("payments:success"))
        cancel_url = self.build_abs_url(url=reverse_lazy("payments:home"))

        logger.info("stripe retrieved order(👩🏻‍⚖️) from session as: %s", order)
        logger.info("stripe amount in usd(💵):$%s", amount)
        logger.info("stripe success_url(🙌):%s", success_url)
        logger.info("stripe cancel_url(🛑):%s", cancel_url)

        # veer refer to this link
        # https://stripe.com/docs/api/checkout/sessions/create
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=order.email,
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
                client_reference_id=client_reference_id,
            )
        except Exception as e:
            return str(e)

        return redirect(checkout_session.url, code=303)


class PaymentSuccessView(TemplateView):
    template_name: str = "payments/payment_success.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        mp_data = self.request.GET

        logger.info("mercado pago says (🤝)", mp_data)

        # payment_id = mp_data.get("payment_id", "")
        order_id = mp_data.get("external_reference", "")
        order = get_object_or_404(Order, id=order_id)
        order.confirm()

        # since order is confirmed we remove it from the session
        try:
            del self.request.session["order"]
        except KeyError:
            pass
        return super().get_context_data(**kwargs)


class PaymentFailView(TemplateView):
    template_name: str = "payments/payment_fail.html"


class PaymentPendingView(TemplateView):
    template_name: str = "payments/payment_pending.html"


class PaymentCancelView(TemplateView):
    """
    TODO: Not sure about this view and endpoint.
    Does it makes sense?
    """

    template_name: str = "payments/payment_cancel.html"


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

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        logger.info("Stripe: Payment confirmed 💰🤑💰")
        logger.info("stripe webhook event(💶): %s", event)
        # We need to send a response to stripe back immediately
        # So order confirmation (especially if it generates pdf or sends email
        # should be handled async or outside the scope of this method
        # TODO: Move order.confirm() outside this method. Just take the order_id from here.
        order_id = event.data.object.client_reference_id
        order = get_object_or_404(Order, id=order_id)
        order.confirm()
        # Saving a copy of the order in your own database.
        # Sending the customer a receipt email.

    return HttpResponse(status=HTTPStatus.OK)


@csrf_exempt
def mercadopago_webhook(request):
    """
    Our internal webhook to receive payment updates from mercado pago.

    A confirmation on this hook is a guarantee that the payment is successful.
    # TODO: May be store the confirmation data in a model or email
    """

    payload = request.body

    logger.info("mercadopago webhook(🤝):%s", payload)

    return HttpResponse(status=HTTPStatus.OK)
