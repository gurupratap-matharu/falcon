"""
Exposes helper methods to draw order data in pdf and other formats.
"""

import logging
from timeit import default_timer as timer

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

from weasyprint import CSS, HTML

logger = logging.getLogger(__name__)


def burn_invoice_pdf(target=None, context=None):
    """
    Render the order to plain old HTML and burn it to a pdf on the provided object.
    """
    start = timer()

    logger.info("burning invoice to pdf 🔥...")

    html = render_to_string(template_name="orders/invoice.html", context=context)
    stylesheet = CSS(finders.find("assets/css/invoice.css"))
    HTML(string=html).write_pdf(target, stylesheets=[stylesheet])

    end = timer()

    logger.info("burning invoice to pdf 🔥 took:%0.2f seconds..." % (end - start))

    return target


def burn_ticket_pdf(request, target, order):
    """
    Render the final boarding ticket with QR code into a pdf.
    Usually this is used to send over email as an attachment

    TODO: Implement QR code to verify the ticket
    """

    start = timer()

    template_name = "orders/ticket.html"
    base_url = request.build_absolute_uri()

    html = render_to_string(
        template_name,
        {
            "order": order,
            "trip": order.trips.first(),
            "passengers": order.passengers.all(),
        },
    )

    stylesheet = CSS(finders.find("assets/css/ticket.css"))
    render = HTML(string=html, base_url=base_url)

    # We pull the write_pdf attribute like this as directly calling it hangs our lint
    make_pdf = getattr(render, "write_pdf")
    make_pdf(target=target, stylesheets=[stylesheet], presentational_hints=True)

    end = timer()

    logger.info("drawing ticket pdf(🎫) took:%0.2f seconds..." % (end - start))

    return target
