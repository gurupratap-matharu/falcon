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
        - shoot an email with tickets and invoice to the user
        - shoot an email to the company about the booking
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

        user_email, company_email = mail.outbox

        # Check both user and company emails are sent
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(sent_mails, 2)

        # Test user email details

        self.assertEqual(user_email.to, [self.order.email])
        self.assertEqual(user_email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIsNotNone(user_email.body)
        self.assertIsNotNone(user_email.attachments)

        # Check both invoice and ticket are in attachments
        self.assertEqual(len(user_email.attachments), 2)

        # Check email html alternatives
        # html_message, html_format = user_email.alternatives[0]

        # self.assertIsNotNone(html_message)
        # self.assertEqual(html_format, "text/html")

        ticket_filename, ticket_content, ticket_mime_type = user_email.attachments[0]
        invoice_filename, invoice_content, invoice_mime_type = user_email.attachments[1]

        # Check email attachment filename and mime type
        self.assertEqual(ticket_filename, f"Ticket-{self.order.name}.pdf")
        self.assertEqual(ticket_mime_type, "application/pdf")
        self.assertIsInstance(ticket_content, bytes)
        self.assertIsNotNone(ticket_content)

        self.assertEqual(invoice_filename, f"Invoice-{self.order.name}.pdf")
        self.assertEqual(invoice_mime_type, "application/pdf")
        self.assertIsInstance(invoice_content, bytes)
        self.assertIsNotNone(invoice_content)

        # Test company email details
        self.assertEqual(company_email.to, [self.order_items[0].trip.company.email])
        self.assertEqual(company_email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIsNotNone(company_email.body)
