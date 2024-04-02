import uuid

from django.conf import settings
from django.core import mail
from django.http import Http404
from django.test import TestCase

from orders.factories import OrderFactory, OrderItemFactory
from orders.services import order_confirmed


class OrderConfirmedTests(TestCase):
    """
    Test suite for order confirmation service

    This is a very important test case. This logic runs when we get a payment confirmation
    on our webhooks. We basically...
        - mark the order as paid
        - mark the seats from onhold -> booked
        - save the payment_id to the order for reference
        - shoot an email with tickets
    """

    def setUp(self):
        self.order = OrderFactory()
        self.order_items = OrderItemFactory.create_batch(size=2, order=self.order)

    def test_order_confirmation_for_invalid_order_raises_404(self):
        order_id = uuid.uuid4()  # <-- random order_id
        payment_id = 1234

        with self.assertRaises(Http404):
            mails_sent = order_confirmed(order_id=order_id, payment_id=payment_id)
            self.assertEqual(mails_sent, 0)
            self.assertEqual(len(mail.outbox), 0)

    def test_order_confirmation_sends_tickets_via_email(self):
        # Initially outbox should be empty
        self.assertEqual(len(mail.outbox), 0)

        # Create the Order
        order_id = str(self.order.id)
        sent_mails = order_confirmed(order_id=order_id, payment_id=12345)

        # Check email is sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(sent_mails, 1)

        email = mail.outbox[0]

        # Check email details
        self.assertEqual(email.subject, "Your tickets from Kpiola")
        self.assertEqual(email.to, [self.order.email])
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIsNotNone(email.attachments)

        # Check email html alternatives
        html_message, html_format = email.alternatives[0]

        self.assertIsNotNone(html_message)
        self.assertEqual(html_format, "text/html")

        filename, content, mime_type = email.attachments[0]

        # Check email attachment filename and mime type
        self.assertEqual(filename, f"Ticket-{self.order.name}.pdf")
        self.assertEqual(mime_type, "application/pdf")
