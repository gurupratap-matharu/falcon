"""
Exposes helper methods to draw order data in pdf and other formats.
"""
import logging
from timeit import default_timer as timer

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

from weasyprint import CSS, HTML

logger = logging.getLogger(__name__)


def burn_invoice_pdf(context=None):
    """
    Render a pdf invoice for an order
    """
    start = timer()
    logger.info("burning invoice to pdf 🔥...")

    template_name = "orders/invoice.html"
    css_path = finders.find("assets/css/invoice.css")

    html = render_to_string(template_name, context)
    stylesheet = CSS(css_path)
    pdf = HTML(string=html).write_pdf(stylesheets=[stylesheet])

    end = timer()
    logger.info("took:%0.2f seconds..." % (end - start))

    return pdf


def burn_ticket_pdf(context=None):
    """
    Render the final boarding ticket with QR code into a pdf.
    """

    start = timer()
    logger.info("burning ticket to pdf 🔥...")

    template_name = "orders/ticket.html"
    css_path = finders.find("assets/css/ticket.css")

    html = render_to_string(template_name, context)
    stylesheet = CSS(css_path)

    pdf = HTML(string=html).write_pdf(
        stylesheets=[stylesheet], presentational_hints=True
    )

    end = timer()
    logger.info("took:%0.2f seconds..." % (end - start))

    return pdf
