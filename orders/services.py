import logging
from timeit import default_timer as timer

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from orders.drawers import burn_invoice_pdf, burn_ticket_pdf
from orders.models import Order, OrderItem

logger = logging.getLogger(__name__)
domain = Site.objects.get_current().domain


def order_created(order_id):
    """
    Send an e-mail notification to the payer confirming the creation of the order
    with an order id.

    The order at this phase is still unpaid and payment is yet to be done.
    """
    start = timer()

    order = get_object_or_404(Order.objects.prefetch_related("items"), id=order_id)
    items = OrderItem.objects.filter(order=order).select_related("trip")
    context = {"order": order, "items": items}

    subject = "Your Invoice from Kpiola"
    message = (
        f"Thanks for your order {order.name},\n\n"
        f"Attached is your invoice.\n"
        f"Your order ID is {order.id}."
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    # Create pdf invoice using weasy print
    content = burn_invoice_pdf(context=context)

    # Attach pdf invoice to email object
    email.attach(
        filename=f"Invoice-{order.name}.pdf",
        content=content,
        mimetype="application/pdf",
    )

    # Attach html version as an alternative
    html_message = render_to_string(
        template_name="orders/emails/compiled/invoice.html", context=context
    )
    email.attach_alternative(content=html_message, mimetype="text/html")

    # Send email
    logger.info("sending invoice via email 💌...")
    mail_sent = email.send(fail_silently=False)

    end = timer()
    logger.info("order_created(📜) took: %0.2f seconds!" % (end - start))

    return mail_sent


def order_confirmed(order_id, payment_id):
    """
    When an order is successfully confirmed / paid we
        - book all seats in an order with passengers
        - send tickets via e-mail to the payer.
    """

    start = timer()

    # Get the order details
    order = get_object_or_404(Order.objects.prefetch_related("items"), id=order_id)
    items = OrderItem.objects.filter(order=order).select_related("trip")

    item = items.first()  # <-- fix this

    qr_url = f"https://{domain}{item.get_checkin_url()}"
    context = dict(order=order, item=item, trip=item.trip, qr_url=qr_url)

    # Confirm the order
    logger.info("confirming order...")
    # order.confirm(payment_id=payment_id) # <-- TODO fix this

    # Generate the Email object
    subject = "Your tickets from Kpiola"
    message = (
        f"Thanks for your order {order.name},\n\n"
        f"Attached is your ticket.\n"
        f"Your order ID is {order.id}."
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    # Create pdf ticket using weasy print
    content = burn_ticket_pdf(context=context)

    # Attach pdf ticket to email object
    email.attach(
        filename=f"Ticket-{order.name}.pdf",
        content=content,
        mimetype="application/pdf",
    )

    # Attach html version as an alternative
    html_message = render_to_string(
        template_name="orders/emails/compiled/ticket.html", context=context
    )
    email.attach_alternative(content=html_message, mimetype="text/html")

    # Send email
    logger.info("sending tickets via email 💌...")
    mail_sent = email.send(fail_silently=False)

    end = timer()
    logger.info("order_confirmed(🔒) took: %0.2f seconds!" % (end - start))

    return mail_sent
