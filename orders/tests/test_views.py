import pdb
from datetime import timedelta
from http import HTTPStatus

from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import resolve, reverse_lazy
from django.utils import timezone

from cart.cart import Cart
from orders.forms import OrderForm, PassengerForm
from orders.models import Order, OrderItem, Passenger
from orders.views import OrderCreateView
from trips.factories import LocationFactory, SeatFactory, TripTomorrowFactory
from trips.models import Location, Seat, Trip


class OrderCreateTests(TestCase):
    """
    Test suite for the main and very complex order create view

    Remember veer anytime you try to access OrderCreate view you should have
    these two things
        - 1. A search query in session
        - 2. A trip(s) in cart
    """

    search_query = {
        "trip_type": "round_trip",
        "num_of_passengers": "2",
        "origin": "Alta Gracia",
        "destination": "Anatuya",
        "departure": "23-02-2023",
        "return": "",
    }

    def setUp(self):
        self.origin, self.destination = LocationFactory.create_batch(size=2)
        self.trip = TripTomorrowFactory(
            origin=self.origin, destination=self.destination, status=Trip.ACTIVE
        )
        self.url = reverse_lazy("orders:order_create")
        self.template_name = "orders/order_form.html"

        session = self.client.session
        session["q"] = self.search_query
        session.save()

        # Add trip to cart
        self.client.post(self.trip.get_add_to_cart_url())

    # GET
    def test_order_create_page_works_via_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Order")
        self.assertContains(response, "Passenger")
        self.assertIn("cart", response.context)
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_order_create_url_resolves_ordercreateview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, OrderCreateView.as_view().__name__)

    def test_order_page_renders_order_form_correctly(self):
        response = self.client.get(self.url)

        self.assertIn("form", response.context)
        self.assertIn("formset", response.context)

        self.assertIsInstance(response.context["form"], OrderForm)

    def test_order_page_renders_passenger_formset_correctly(self):
        num_of_passengers = int(self.client.session["q"]["num_of_passengers"])
        response = self.client.get(self.url)
        formset = response.context["formset"]

        self.assertIn("formset", response.context)
        self.assertIsInstance(formset.forms[0], PassengerForm)
        self.assertEqual(formset.total_form_count(), num_of_passengers)
        self.assertEqual(formset.extra, num_of_passengers)

    def test_order_page_contains_cart_in_context(self):
        response = self.client.get(self.url)

        self.assertIn("cart", response.context)
        self.assertIsInstance(response.context["cart"], Cart)

    def test_order_page_redirects_to_home_if_no_query_found_in_session(self):
        # first let's clear the session set in setup()
        session = self.client.session
        session.clear()
        session.save()

        # now hit the order create page directly
        response = self.client.get(self.url)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse_lazy("pages:home"), HTTPStatus.FOUND)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), OrderCreateView.redirect_message)

    def test_order_page_redirects_to_home_if_cart_is_empty(self):
        session = self.client.session
        session.clear()
        session.save()

        # now hit the order create page directly
        response = self.client.get(self.url)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse_lazy("pages:home"), HTTPStatus.FOUND)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), OrderCreateView.redirect_message)

    # POST

    def test_order_creation_for_valid_post_data(self):
        """
        This is an end-to-end kind of test for successful order creation.

        Arrange:
            - We want to initialize a trip with two vacant seats between two locations

        Act:
            - Make a user choose this trip and book both the available seats by placing an order

        Assert:
            - Verify that order is created successfully
            - Verify that passengers are created successfully
            - Verify order <--> passenger relationship formed
            - Verify both seats are booked
            - Verify redirection to payments page
        """

        # First clear the object created in setUp method
        Location.objects.all().delete()
        Trip.objects.all().delete()

        # let's clear the session set in setup()
        session = self.client.session
        session.clear()
        session.save()

        tomorrow = timezone.now() + timedelta(days=1)
        num_of_passengers = 2

        # Create two locations
        origin, destination = LocationFactory.create_batch(size=2)

        # Create a trip between them with two available seats
        trip = TripTomorrowFactory(
            origin=origin, destination=destination, status=Trip.ACTIVE
        )
        SeatFactory.reset_sequence(1)
        SeatFactory.create_batch(size=2, trip=trip, seat_status=Seat.AVAILABLE)

        # Make sure data is correctly created
        trip_from_db = Trip.objects.first()

        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 1)

        self.assertEqual(trip_from_db.seats.count(), 2)
        self.assertEqual(trip_from_db.seats_available, 2)
        self.assertEqual(trip.origin, origin)
        self.assertEqual(trip.destination, destination)

        # Make sure trip is leaving tomorrow with available seats
        seat_1, seat_2 = trip.seats.all()

        self.assertEqual(trip.departure.date(), tomorrow.date())
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)

        # Let's build fake session data to simulate as if user tried searching
        # this trip to book it
        search_query = {
            "trip_type": "round_trip",
            "num_of_passengers": str(num_of_passengers),
            "origin": origin.name,
            "destination": destination.name,
            "departure": tomorrow.strftime("%d-%m-%Y"),
            "return": "",
        }

        session = self.client.session
        session["q"] = search_query
        session.save()

        # Cool now we need to simulate as if user has added our trip to the cart
        self.client.post(trip.get_add_to_cart_url())
        # User is on the order page and has filled in all the details

        # IMP Veer don't create passenger or order data using factories as it will be
        # saved in the DB. We want to create this data via post request
        payer_name = "Gisela Vidal"
        payer_email = "gisela@email.com"
        payer_residence = "AR"

        data = {
            # management_form data
            "form-TOTAL_FORMS": 2,  # <- Two passenger forms
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 0,
            "form-MAX_NUM_FORMS": 1000,
            # Selected seats
            f"seats{trip.id}": "1, 2",
            # Formset
            # Passenger 1 data
            "form-0-document_type": "PASSPORT",
            "form-0-document_number": "9988776655",
            "form-0-nationality": "AR",
            "form-0-first_name": "Gisela",
            "form-0-last_name": "vidal",
            "form-0-gender": "F",
            "form-0-birth_date": "03/03/1989",
            "form-0-phone_number": "1122334455",
            # Passenger 2 data
            "form-1-document_type": "PASSPORT",
            "form-1-document_number": "12345678",
            "form-1-nationality": "IN",
            "form-1-first_name": "Veer",
            "form-1-last_name": "Playing",
            "form-1-gender": "M",
            "form-1-birth_date": "03/07/1985",
            "form-1-phone_number": "1150254191",
            # Order Form data
            "name": payer_name,
            "email": payer_email,
            "residence": payer_residence,
        }

        # Cool. Now let's submit the order form via post
        # Order creation will redirect to payments page so make `follow=True`
        response = self.client.post(self.url, data=data, follow=True)

        # Verify that seats are put on hold since order is yet unpaid
        trip = Trip.objects.first()
        seat_1, seat_2 = trip.seats.all()

        self.assertEqual(seat_1.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_2.seat_status, Seat.ONHOLD)

        # Verify order is created correctly and unpaid
        order = Order.objects.first()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.name, payer_name)
        self.assertEqual(order.email, payer_email)
        self.assertEqual(order.residence, payer_residence)

        # Verify order is unpaid
        self.assertFalse(order.paid)
        self.assertEqual(order.payment_id, "")
        self.assertEqual(order.discount, 0)
        self.assertIsNone(order.coupon)

        # Verify order passenger relationship
        self.assertEqual(order.passengers.count(), 2)

        # Verify passengers are created correctly
        self.assertEqual(Passenger.objects.count(), 2)

        # Verify redirection
        expected_url = reverse_lazy("payments:home")
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        # Verify OrderItems created correctly
        order_item = OrderItem.objects.first()

        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.trip, trip)
        self.assertEqual(order_item.price, trip.price)
        self.assertEqual(order_item.quantity, num_of_passengers)
        self.assertEqual(order_item.seats, "1, 2")

        # Verify Cart is cleared
        self.assertNotIn("cart", session)
        self.assertIsNone(session.get("cart"))

        # Verify Order id is in session
        # IMP access session propery again like this...
        session = self.client.session
        self.assertIn("order", session)
        self.assertEqual(session.get("order"), str(order.id))

        # Verify that order creation email has been sent
        # Test that an email has been sent.
        # Verify that the subject of the first message is correct.
        # Check page redirected to home after success
        self.assertEqual(len(mail.outbox), 1)

        subject = f"Order nr. {order.id}"
        body = (
            f"Dear {order.name},\n\n"
            f"You have successfully placed an order.\n"
            f"Your order ID is {order.id}."
        )
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
        self.assertEqual(response.request["PATH_INFO"], reverse_lazy("payments:home"))

    def test_order_validation_errors_for_invalid_post_data(self):
        # TODO
        pass

    def test_expired_session_marks_seats_as_avaiable_again(self):
        self.fail()

    def test_order_creation_for_invalid_seat_numbers_redirects_with_message(self):
        self.fail()

    def test_order_creation_for_invalid_trip_redirects_with_message(self):
        self.fail()

    def test_valid_coupon_is_applied_to_order_successfully(self):
        self.fail()

    def test_invalid_coupon_redirects_with_message(self):
        self.fail()
