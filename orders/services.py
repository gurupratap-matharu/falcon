import logging
from io import BytesIO
from timeit import default_timer as timer

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

import weasyprint

from .drawers import burn_order_pdf
from .models import Order

logger = logging.getLogger(__name__)


def order_created(order_id):
    """
    Send an e-mail notification to the payer confirming the creation of the order
    with an order id.

    The order at this phase is still unpaid and payment is yet to be done.
    """
    start = timer()

    order = get_object_or_404(Order, id=order_id)

    subject = f"Order nr. {order.id}"
    message = (
        f"Dear {order.name},\n\n"
        f"You have successfully placed an order.\n"
        f"Your order ID is {order.id}."
    )
    mail_sent = send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        fail_silently=False,
    )

    end = timer()
    logger.info("order_created(📜) took: %0.2f seconds!" % (end - start))

    return mail_sent


def order_confirmed(order_id, payment_id):
    """
    When an order is successfully confirmed / paid we

        - book all seats in an order with passengers
        - send an invoice via e-mail to the payer.

    """
    start = timer()

    # 1 Get the order details and confirm it
    order = get_object_or_404(Order, id=order_id)
    order.confirm(payment_id=payment_id)

    # 2 Generate the Email object
    subject = f"FalconHunt - Invoice no. {order.id}"
    message = "Please, find attached the invoice for your recent purchase."
    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])

    # 3 Create pdf doc using weasy print
    out = BytesIO()
    burn_order_pdf(on=out, order=order)

    # 4 Attach pdf to email object
    email.attach(
        filename=f"invoice_{order.name}.pdf",
        content=out.getvalue(),
        mimetype="application/pdf",
    )

    # 5 Send email
    email.send(fail_silently=False)

    end = timer()
    logger.info("order_confirmed(🔒) took: %0.2f seconds!" % (end - start))
