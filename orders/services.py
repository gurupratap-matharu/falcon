import logging
from timeit import default_timer as timer

from django.conf import settings
from django.core.mail import send_mail

from .models import Order

logger = logging.getLogger(__name__)


def order_created(order_id):
    """
    Send an e-mail notification to the payer confirming the creation of the order
    with an order id.

    The order at this phase is still unpaid and payment is yet to be done.
    """
    start = timer()

    order = Order.objects.get(id=order_id)

    subject = f"Order nr. {order.id}"
    message = (
        f"Dear {order.name},\n\n"
        f"You have successfully placed an order.\n"
        f"Your order ID is {order.id}."
    )
    mail_sent = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])

    end = timer()
    logger.info("order_created(📜) took: %0.2f seconds!" % (end - start))

    return mail_sent


def order_confirmed(order_id):
    """
    When an order is successfully confirmed / paid we run this flow to
        - book all seats in an order with passengers
        - send an e-mail notification to the payer.
    """
    start = timer()

    order = Order.objects.get(id=order_id)
    order.confirm()

    subject = f"Your Tickets for Order nr. {order.id}"
    message = (
        f"Dear {order.name},\n\n"
        f"Your tickets have been booked 🙌.\n"
        f"Please find them attached."
    )
    mail_sent = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])
    end = timer()

    logger.info("order_confirmed(🔒) took: %0.2f seconds!" % (end - start))
    return mail_sent
