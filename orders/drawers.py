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

import weasyprint

logger = logging.getLogger(__name__)


def burn_order_pdf(on=None, order=None):
    """
    Render the order to plain old HTML and burn it to a pdf on the provided object.
    """
    start = timer()

    html = render_to_string("orders/order_pdf.html", {"order": order})
    stylesheet = weasyprint.CSS(settings.STATIC_ROOT / "assets" / "css" / "pdf.css")
    weasyprint.HTML(string=html).write_pdf(on, [stylesheet])  # type:ignore

    end = timer()
    logger.info("drawing order pdf(🎨) took:%0.2f seconds..." % (end - start))

    return on
