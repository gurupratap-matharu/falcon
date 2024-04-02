import logging
from timeit import default_timer as timer

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from orders.drawers import burn_invoice_pdf, burn_ticket_pdf
from orders.models import Order, OrderItem

logger = logging.getLogger(__name__)

current_site = Site.objects.get_current()


def order_confirmed(order_id, payment_id):
    """
    When an order is successfully confirmed / paid we
        - book all seats in an order with passengers
        - send tickets via e-mail to the payer.
        - send notification email to the bus company
    """

    start = timer()

    # Get the order details
    order = get_object_or_404(Order.objects.prefetch_related("items"), id=order_id)
    items = OrderItem.objects.filter(order=order).select_related("trip")

    item = items.first()  # <-- fix this

    # qr_url = f"https://{current_site.domain}{item.get_checkin_url()}"
    # context = dict(order=order, item=item, trip=item.trip, qr_url=qr_url)

    # Confirm the order
    logger.info("confirming order...")
    order.confirm(payment_id=payment_id)

    context = {"order": order, "item": item, "current_site": current_site}

    # User Email
    subject_path = "orders/emails/booking_confirmed_subject.txt"
    body_path = "orders/emails/booking_confirmed_message.txt"

    subject = render_to_string(subject_path, context).strip()
    body = render_to_string(body_path, context).strip()

    user_email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email, settings.DEFAULT_TO_EMAIL],
    )

    # Attach html version as an alternative
    # html_message = render_to_string(
    #     template_name="orders/emails/booking_confirmed_message.html", context=context
    # )
    # user_email.attach_alternative(content=html_message, mimetype="text/html")

    # Create pdf ticket using weasy print
    ticket = burn_ticket_pdf(context=context)

    # Attach pdf ticket to email
    user_email.attach(
        filename=f"Ticket-{order.name}.pdf",
        content=ticket,
        mimetype="application/pdf",
    )

    # Create pdf invoice using weasy print
    invoice = burn_invoice_pdf(context=context)

    # Attach pdf invoice to email
    user_email.attach(
        filename=f"Invoice-{order.name}.pdf",
        content=invoice,
        mimetype="application/pdf",
    )

    # Company Notification Email
    subject_path = "orders/emails/booking_confirmed_company_subject.txt"
    body_path = "orders/emails/booking_confirmed_company_message.txt"

    subject = render_to_string(subject_path, context).strip()
    body = render_to_string(body_path, context).strip()
    # company_email = item.trip.company.email  # TODO: disabled to avoid spams
    company_email = settings.DEFAULT_TO_EMAIL  # TODO: Change this later

    company_email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[company_email],
    )

    # Send both emails in one go
    logger.info("sending booking emails...")

    connection = mail.get_connection()
    mails_sent = connection.send_messages([user_email, company_email])

    end = timer()
    logger.info("order_confirmed(🔒) took: %0.2f seconds!" % (end - start))

    return mails_sent
