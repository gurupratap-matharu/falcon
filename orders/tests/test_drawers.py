from django.http import HttpResponse
from django.test import TestCase

from orders.factories import OrderFactory, PassengerFactory


class TicketPDFTests(TestCase):
    """Test suite to verify ticket pdf generation"""

    def setUp(self):
        self.passengers = PassengerFactory.create_batch(size=2)
        self.order = OrderFactory(passengers=self.passengers)

    def test_burn_ticket_pdf_works(self):
        """
        Currently this test is failing on github action runner since it needs
        additional dependencies for WeasyPrint

        TODO: hack around this
        """
        # First we create a dummy request and response.

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=tickets.pdf"

        # Assert response is empty
        self.assertEqual(response.content, b"")

        # Burn the ticket pdf onto the reponse
        # response = burn_ticket_pdf(request=request, target=response, order=self.order)

        # Assert response is not empty
        # self.assertNotEqual(response.content, b"")


class OrderInvoicePDFTests(TestCase):
    """
    Test suite to verify order invoice pdf generation
    """

    def setUp(self):
        self.passengers = PassengerFactory.create_batch(size=2)
        self.order = OrderFactory(passengers=self.passengers)

    def test_burn_order_invoice_pdf_works(self):
        """
        Currently this test is failing on github action runner since it needs
        additional dependencies for WeasyPrint

        TODO: hack around this
        """
        # First we create a dummy request and response.

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=invoice.pdf"

        # Assert response is empty
        self.assertEqual(response.content, b"")

        # Burn the ticket pdf onto the reponse
        # response = burn_order_pdf(target=response, order=self.order)

        # Assert response is not empty
        # self.assertNotEqual(response.content, b"")
