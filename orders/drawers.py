"""
Exposes helper methods to draw order data in pdf and other formats.

Blocker Note:
    Veer the weasy print module is slowing down our linter on vscode considerably
    and we have no quick fix at the moment. The immediate solution is to move all
    weasy print write_pdf() calls in a standalone script to keep the linting and
    formatting of other files fast.

    Not sure what causes this. But its just the write_pdf() method of weasyprint.
    I am unable to find a way to ignore it somehow. vscode stucks on analysing files
    for several seconds.
"""

import logging
from timeit import default_timer as timer

from django.conf import settings
from django.template.loader import render_to_string

from weasyprint import CSS, HTML

logger = logging.getLogger(__name__)


def burn_order_pdf(target=None, order=None):
    """
    Render the order to plain old HTML and burn it to a pdf on the provided object.
    """
    start = timer()

    html = render_to_string("orders/invoice.html", {"order": order})

    render = HTML(string=html)
    stylesheet = CSS(settings.STATIC_ROOT / "assets" / "css" / "pdf.css")

    # We pull the write_pdf attribute like this as directly calling it hangs our lint
    make_pdf = getattr(render, "write_pdf")

    make_pdf(target, [stylesheet])

    end = timer()
    logger.info("drawing order pdf(🎨) took:%0.2f seconds..." % (end - start))

    return target


def burn_ticket_pdf(request, target, order):
    """
    Render the final boarding ticket with QR code into a pdf.
    Usually this is used to send over email as an attachment

    TODO: Implement QR code to verify the ticket
    """

    start = timer()

    template_name = "orders/ticket.html"  # <-- change this
    css_path = settings.STATIC_ROOT / "assets" / "css" / "ticket.css"  # <-- change this

    base_url = request.build_absolute_uri()

    html = render_to_string(
        template_name,
        {
            "order": order,
            "trip": order.trips.first(),
            "passengers": order.passengers.all(),
        },
    )

    stylesheet = CSS(css_path)
    render = HTML(string=html, base_url=base_url)

    # We pull the write_pdf attribute like this as directly calling it hangs our lint
    make_pdf = getattr(render, "write_pdf")
    make_pdf(target=target, stylesheets=[stylesheet], presentational_hints=True)

    end = timer()

    logger.info("drawing ticket pdf(🎫) took:%0.2f seconds..." % (end - start))

    return target
