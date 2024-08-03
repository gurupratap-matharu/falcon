import logging
from timeit import default_timer as timer

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from django_weasyprint.utils import django_url_fetcher
from weasyprint import HTML

from orders.models import Order

logger = logging.getLogger(__name__)


def burn_pdf(template_name, context) -> bytes:
    """
    Renders a django template to a pdf file.
    """

    pdf = HTML(
        string=render_to_string(template_name, context),
        url_fetcher=django_url_fetcher,
        base_url="file://",
    ).write_pdf()

    return pdf


def build_context(order_id) -> dict:
    """
    Given an order id builds a context that can be use in email body and pdf generation.
    """

    order = get_object_or_404(Order, id=order_id)
    item = order.items.select_related("trip", "origin", "destination").first()
    trip = item.trip
    company = trip.company
    passengers = order.passengers.all()
    qr_url = f"https://kpiola.com.ar/{item.get_checkin_url()}"

    context = dict(
        order=order,
        item=item,
        trip=trip,
        origin=item.origin,
        destination=item.destination,
        company=company,
        code=str(order.id).split("-")[-1],
        trip_code=str(trip.id).split("-")[-1],
        passengers=passengers,
        qr_url=qr_url,
    )

    logger.info("context:%s" % context)
    return context


def order_confirmed(order_id, payment_id):
    """
    When an order is successfully confirmed / paid we
        - book all seats in an order with passengers
        - send tickets via e-mail to the payer.
        - send notification email to the bus company
    """

    start = timer()

    context = build_context(order_id=order_id)
    order = context["order"]
    item = context["item"]

    # Confirm the order
    order.confirm(payment_id=payment_id)

    # User Email
    subject_path = "orders/emails/booking_confirmed_subject.txt"
    body_path = "orders/emails/booking_confirmed_message.txt"

    subject = render_to_string(subject_path, context).strip()
    body = render_to_string(body_path, context).strip()

    user_email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
        cc=[settings.DEFAULT_TO_EMAIL],
    )

    # Attach html version as an alternative
    # html_message = render_to_string(
    #     template_name="orders/emails/booking_confirmed_message.html", context=context
    # )
    # user_email.attach_alternative(content=html_message, mimetype="text/html")

    # Create pdfs for ticket and invoice
    ticket = burn_pdf(template_name="orders/ticket.html", context=context)
    invoice = burn_pdf(template_name="orders/invoice.html", context=context)

    # Attach pdfs to email
    user_email.attach(
        filename=f"Ticket-{order.name}.pdf",
        content=ticket,
        mimetype="application/pdf",
    )
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
    company_email = item.trip.company.email

    company_email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[company_email],
        cc=[settings.DEFAULT_TO_EMAIL],
    )

    # Send both emails in one go
    logger.info("sending booking emails...")

    connection = mail.get_connection()
    mails_sent = connection.send_messages([user_email, company_email])

    end = timer()
    logger.info("order_confirmed(🔒) took: %0.2f seconds!" % (end - start))

    return mails_sent
