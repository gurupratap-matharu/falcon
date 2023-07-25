import pdb
import uuid

from django.conf import settings
from django.core import mail
from django.http import Http404
from django.test import TestCase

from orders.factories import OrderFactory, OrderItemFactory
from orders.services import order_created


class OrderCreatedTests(TestCase):
    """
    Test suite for order creation service
    """

    def setUp(self):
        self.order = OrderFactory()
        self.order_items = OrderItemFactory.create_batch(size=2, order=self.order)

    def test_order_creation_for_invalid_order_raises_404(self):
        order_id = uuid.uuid4()  # <-- random order_id

        with self.assertRaises(Http404):
            order_created(order_id=order_id)

    def test_order_creation_sends_email(self):
        # Initially outbox should be empty
        self.assertEqual(len(mail.outbox), 0)

        # Create the Order
        order_id = str(self.order.id)
        order_created(order_id=order_id)

        # Check email is sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        # Check email details
        self.assertEqual(email.subject, "Your Invoice from Falcon")
        self.assertEqual(email.to, [self.order.email])
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIsNotNone(email.attachments)

        # Check email html alternatives
        html_message, html_format = email.alternatives[0]

        self.assertIsNotNone(html_message)
        self.assertEqual(html_format, "text/html")

        filename, content, mime_type = email.attachments[0]

        # Check email attachment filename and mime type
        self.assertEqual(filename, f"Invoice-{self.order.name}.pdf")
        self.assertEqual(mime_type, "application/pdf")
