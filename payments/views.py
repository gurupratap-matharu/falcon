import logging
from datetime import timedelta
from http import HTTPStatus
from typing import Any, Dict

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

import mercadopago
import stripe

from orders.models import Order
from orders.services import order_confirmed

from .models import WebhookMessage

logger = logging.getLogger(__name__)

mercado_pago = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentView(TemplateView):
    """A simple view that shows all payment options for our project"""

    template_name: str = "payments/payment.html"
    order: Order = None
    redirect_message = "Your session has expired. Please search again 🙏"

    def dispatch(self, request, *args, **kwargs):
        """
        If no order in session then redirect user to home.
        """

        order = request.session.get("order")

        if not order:
            messages.info(request, self.redirect_message)
            return redirect("pages:home")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        order_id = self.request.session.get("order")

        context = super().get_context_data(**kwargs)

        context["order"] = self.order = get_object_or_404(Order, id=order_id)
        context["preference"] = self.get_mercado_pago_preference()
        context["mp_public_key"] = settings.MP_PUBLIC_KEY

        return context

    def get_mercado_pago_preference(self):
        """Get reponse from Mercado Pago for preference (item) data."""

        uri = self.request.build_absolute_uri
        order = self.order
        unit_price = float(order.get_total_cost() / 1000)  # <-- Minimizing this for MP

        picture_url = uri(static("assets/img/bus/bus4.avif"))
        success = uri(reverse_lazy("payments:mercadopago_success"))
        failure = uri(reverse_lazy("payments:fail"))
        pending = uri(reverse_lazy("payments:pending"))
        notification_url = (
            uri(reverse_lazy("payments:mercadopago_webhook")) + f"&order_id={order.id}"
        )

        logger.info("success: %s", success)
        logger.info("failure: %s", failure)
        logger.info("pending: %s", pending)
        logger.info("picture_url: %s", picture_url)
        logger.info("notification_url: %s", notification_url)

        # Create mercado page preference
        # veer we use quantity as always 1 with full order price 😉
        preference_data = {
            "items": [
                {
                    "id": str(order.id),
                    "title": f"Bus ticket for {order.name}",
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
            "statement_descriptor": "Kpiola",
            "external_reference": str(order.id),
            "binary_mode": True,
        }

        preference = mercado_pago.preference().create(preference_data)

        logger.debug("MP preference_data:%s", preference_data)
        logger.debug("MP response(💰):%s", preference)

        return preference["response"]


class CheckoutView(TemplateView):
    """
    Stripe checkout view

    This view actually doesn't render any template. It just receives post data
    from payment options page and creates a stripe checkout session and redirects to it.

    The user is routed back to our site based on the payment status.

    # TODO: Based on the coupon discount of an order we can actually pass stripe the original charge amount
    # and the coupon discount. At this moment we are not doing this. Instead we send
    # the final discounted full amount of an order in usd to stripe. We did this as we are
    # not sure if it benefits us and if our other payment provider mercado pago provides such
    # a functionality.
    """

    http_method_names = ["post"]
    template_name: str = "payments/checkout.html"  # <-- veer this is dummy

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, id=self.request.session["order"])
        client_reference_id = str(order.id)
        amount = int(order.get_total_cost_usd() * 100)

        success_url = request.build_absolute_uri(reverse_lazy("payments:success"))
        cancel_url = request.build_absolute_uri(reverse_lazy("payments:home"))

        logger.info("stripe retrieved order(👩🏻‍⚖️) from session as: %s", order)
        logger.info("stripe amount in usd cents(💵):$%s", amount)
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
        context = super().get_context_data(**kwargs)
        # We store the order id in session to generate the ticket pdf if requested
        # before clearing the session as user might wish to book another ticket
        order_id = self.request.session.get("order")
        order = get_object_or_404(Order.objects.select_related(), id=order_id)

        context["order"] = order
        context["calendar_link"] = self.get_calendar_link(order)

        # next since order is confirmed we remove it from the session
        # try:
        #     del self.request.session["order"]
        # except KeyError:
        #     # TODO: technically here veer you should redirect as its not a valid case!
        #     pass

        return context

    def get_calendar_link(self, order):
        """
        This method generates the google calendar link for a trip.
        TODO:
            - Add timezone to the url
            - Currently link takes trip origin (departure time) -> destination (arrival time)
            - Modify this if user books intermediate stops.
        """

        item = order.items.first()

        try:
            trip = item.trip
        except AttributeError as e:
            logger.warn(e)
            return ""

        else:
            origin, destination = trip.origin, trip.destination
            departure = trip.departure.strftime("%Y%m%dT%H%M%S")
            arrival = trip.arrival.strftime("%Y%m%dT%H%M%S")
            base_url = "https://calendar.google.com/calendar/r/eventedit"

            return f"{base_url}?text=BusTrip+{origin}+-+{destination}&dates={departure}/{arrival}"


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
@require_POST
def stripe_webhook(request):
    """
    Our internal webhook registered with stripe which listens for payment
    notifications.

    A confirmation on this hook is a guarantee that the payment is successful.
    """

    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = settings.STRIPE_WEBHOOK_SIGNING_SECRET
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    payload = request.body
    event = None

    logger.debug("stripe webhook:payload:%s, sig_header:%s", payload, sig_header)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

    except ValueError as e:
        # Invalid payload
        logger.warning("Invalid payload received in stripe webhook: %s" % e)
        return HttpResponseBadRequest()

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.warning("Invalid signature received in stripe webhook: %s" % e)
        return HttpResponseForbidden("Invalid signature", content_type="text/plain")

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        logger.info("Stripe:Payment confirmed!")
        logger.info("Stripe:Webhook event(💶): %s", event)

        last_week = timezone.now() - timedelta(days=7)
        WebhookMessage.objects.filter(received_at__lte=last_week).delete()

        WebhookMessage.objects.create(
            provider=WebhookMessage.MERCADOPAGO,
            received_at=timezone.now(),
            payload=event,
        )

        order_id = event.data.object.client_reference_id
        payment_id = event.data.object.payment_intent
        order_confirmed(order_id=order_id, payment_id=payment_id)

    return HttpResponse(status=HTTPStatus.OK)


@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    """
    Webhook to receive payment updates from mercado pago.
    A confirmation on this hook is a guarantee that the payment is successful.
    """

    logger.info("mercadopago webhook request.GET(🤝):%s", request.GET)
    logger.info("mercadopago webhook request.POST(🤝):%s", request.POST)
    logger.info("mercadopago webhook request.body(🤝):%s", request.body)

    return HttpResponse(status=HTTPStatus.OK)


def mercadopago_success(request):
    """
    Parses the query parameters sent by mercado pago when a payment is succesful
    and routes to our PaymentSuccess endpoint. By itself this view does not render any template
    but is just an intermediate processing step.

    This is not a webhook of mercado pago. My understanding is that mercado pago is appending
    payment response as query params to the `success_url` via GET request.

    At the time of implementation I realise that it might not be safe to show mercado pago
    payment details right in the query parameters.

    An example of successful query params is like this...

    /payments/success/?collection_id=54650347595&collection_status=approved&payment_id=54650347595&status=approved&external_reference=7a231700-d000-47d0-848b-65ff914a9a3e&payment_type=account_money&merchant_order_id=7712864656&preference_id=1272408260-35ff1ef7-3eb8-4410-b219-4a98ef386ac0&site_id=MLA&processing_mode=aggregator&merchant_account_id=null
    """

    mercadopago_response = request.GET
    msg = "mercado pago says(🤝):%s" % mercadopago_response
    logger.info(msg) if mercadopago_response else logger.warn(msg)

    order_id = mercadopago_response.get("external_reference")
    status = mercadopago_response.get("status")
    payment_id = mercadopago_response.get("payment_id")

    if (status == "approved") and order_id:
        logger.info("mercadopago(🤝) payment successful!!!")

        # Remove webhook messages more than 1 week old
        last_week = timezone.now() - timedelta(days=7)
        WebhookMessage.objects.filter(received_at__lte=last_week).delete()

        WebhookMessage.objects.create(
            provider=WebhookMessage.MERCADOPAGO,
            received_at=timezone.now(),
            payload=mercadopago_response,
        )

        order_confirmed(order_id=order_id, payment_id=payment_id)

        return redirect(reverse_lazy("payments:success"))

    return redirect(reverse_lazy("payments:fail"))
