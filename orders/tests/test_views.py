import uuid
from datetime import timedelta
from http import HTTPStatus

from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import resolve, reverse_lazy
from django.utils import timezone

from cart.cart import Cart
from orders.factories import OrderFactory, OrderItemFactory
from orders.forms import OrderForm, PassengerForm
from orders.models import Order, OrderItem, Passenger
from orders.views import OrderCreateView, order_cancel
from trips.factories import LocationFactory, SeatFactory, TripTomorrowFactory
from trips.models import Seat, Trip


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


class OrderCreatePostTests(TestCase):
    """
    Test suite to verify Order Creation.
    """

    @classmethod
    def setUpTestData(cls):
        print("running setUpTestData...")
        cls.tomorrow = timezone.now() + timedelta(days=1)
        cls.num_of_passengers = 2

        cls.url = reverse_lazy("orders:order_create")
        cls.success_url = reverse_lazy("payments:home")
        cls.template_name = "orders/order_form.html"
        cls.redirect_template_name = "payments/payment.html"

        cls.origin, cls.destination = LocationFactory.create_batch(size=2)
        cls.trip = TripTomorrowFactory(
            origin=cls.origin, destination=cls.destination, status=Trip.ACTIVE
        )
        SeatFactory.reset_sequence(1)
        SeatFactory.create_batch(size=2, trip=cls.trip, seat_status=Seat.AVAILABLE)

    def setUp(self):
        """Build the session data for each test"""

        print("running setUp...")

        # Search query
        session = self.client.session
        session["q"] = self.build_search_query()
        session.save()

        # Cart
        self.client.post(self.trip.get_add_to_cart_url())

        self.data = self.build_form_data()

    def build_search_query(self):
        """Helper method to just build a user trip search query"""

        q = {
            "trip_type": "round_trip",
            "num_of_passengers": str(self.num_of_passengers),
            "origin": f"{self.origin.name}",
            "destination": f"{self.destination.name}",
            "departure": self.tomorrow.strftime("%d-%m-%Y"),
            "return": "",
        }
        return q

    def build_form_data(self):
        """Helper method to construct the order form post data"""

        # IMP Veer don't create passenger or order data using factories as it will be
        # saved in the DB. We want to create this data via post request

        data = {
            # management_form data
            "form-TOTAL_FORMS": 2,  # <- Two passenger forms
            "form-INITIAL_FORMS": 0,
            "form-MIN_NUM_FORMS": 0,
            "form-MAX_NUM_FORMS": 1000,
            # Selected seats
            f"seats{self.trip.id}": "1, 2",
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
            "name": "Gisela Vidal",
            "email": "gisela@email.com",
            "residence": "AR",
        }

        return data

    def test_order_success_redirects_to_payments(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        self.assertRedirects(
            response=response,
            expected_url=self.success_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.redirect_template_name)
        self.assertContains(response, "Payment")
        self.assertNotContains(response, "Hi I should not be on this page")
        self.assertIsInstance(response.context["order"], Order)

    def test_order_success_creates_order_correctly(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        # Verify that order is created and unpaid
        order = Order.objects.first()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.name, self.data["name"])
        self.assertEqual(order.email, self.data["email"])
        self.assertEqual(order.residence, self.data["residence"])

        # Verify order is unpaid
        self.assertFalse(order.paid)
        self.assertEqual(order.payment_id, "")
        self.assertEqual(order.discount, 0)
        self.assertIsNone(order.coupon)

        # Verify order passenger relationship
        self.assertEqual(order.passengers.count(), 2)

        # Verify passengers are created correctly
        self.assertEqual(Passenger.objects.count(), 2)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_order_success_creates_order_items_correctly(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        # Verify OrderItems created correctly
        order = Order.objects.first()
        order_item = OrderItem.objects.first()
        trip = Trip.objects.first()

        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.trip, trip)
        self.assertEqual(order_item.price, trip.price)
        self.assertEqual(order_item.quantity, self.num_of_passengers)
        self.assertEqual(order_item.seats, "1, 2")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_order_success_puts_seats_on_hold(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        trip = Trip.objects.first()
        seat_1, seat_2 = trip.seats.all()

        self.assertEqual(seat_1.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_2.seat_status, Seat.ONHOLD)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_order_success_clears_the_cart(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        session = self.client.session

        self.assertNotIn("cart", session)
        self.assertIsNone(session.get("cart"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_order_success_places_order_id_in_sessoin(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        order = Order.objects.first()
        session = self.client.session

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("order", session)
        self.assertEqual(session.get("order"), str(order.id))

    def test_order_success_sends_order_creation_email(self):
        response = self.client.post(self.url, data=self.data, follow=True)
        order = Order.objects.first()

        subject = f"Order nr. {order.id}"
        body = (
            f"Dear {order.name},\n\n"
            f"You have successfully placed an order.\n"
            f"Your order ID is {order.id}."
        )
        self.assertEqual(len(mail.outbox), 1)
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



class OrderCancelTests(TestCase):
    """
    Test suite to cancel an order
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
        self.trip = TripTomorrowFactory()
        self.order = OrderFactory()
        self.url = reverse_lazy("orders:order_cancel", args=[str(self.order.id)])
        self.warning_msg = "Your session has expired. Please search again 🙏"

        # Initialize session with search query

        session = self.client.session
        session["q"] = self.search_query
        session.save()

        # Populate the cart with a trip
        self.client.post(self.trip.get_add_to_cart_url())

    def test_cart_and_session_are_not_empty_in_all_order_cancel_tests(self):
        session = self.client.session

        self.assertIn("q", session)
        self.assertIn("cart", session)
        self.assertIsNotNone(session["q"])
        self.assertIsNotNone(session["cart"])

    def test_order_cancel_accepts_only_post_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_order_cancel_url_resolves_order_cancel_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, order_cancel.__name__)

    def test_order_cancel_for_invalid_order_id_throws_404_not_found(self):
        invalid_order_id = uuid.uuid4()
        url = reverse_lazy("orders:order_cancel", args=[str(invalid_order_id)])

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_order_cancel_on_success_clears_the_cart(self):
        response = self.client.post(self.url)
        session = self.client.session

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertNotIn("cart", session)

    def test_order_cancel_on_success_redirects_to_home_with_message(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse_lazy("pages:home"), HTTPStatus.FOUND)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), self.warning_msg)

    def test_order_cancel_releases_seats_to_be_available_again(self):
        # Create a trip with two onhold seats
        outbound_trip, return_trip = TripTomorrowFactory.create_batch(size=2)

        # Create two onhold seats for outbound trip
        SeatFactory.reset_sequence(1)
        seat_1, seat_2 = SeatFactory.create_batch(
            size=2, trip=outbound_trip, seat_status=Seat.ONHOLD
        )

        # Create two onhold seats for return trip
        SeatFactory.reset_sequence(1)
        seat_3, seat_4 = SeatFactory.create_batch(
            size=2, trip=return_trip, seat_status=Seat.ONHOLD
        )

        # Verify that the seats are onhold
        self.assertEqual(seat_1.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_2.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_3.seat_status, Seat.ONHOLD)
        self.assertEqual(seat_4.seat_status, Seat.ONHOLD)

        # Create an order and link it to the trip with order items
        order = OrderFactory()

        outbound_order_item = OrderItemFactory(order=order, trip=outbound_trip)
        outbound_order_item.seats = f"{seat_1.seat_number}, {seat_2.seat_number}"
        outbound_order_item.save()

        return_order_item = OrderItemFactory(order=order, trip=return_trip)
        return_order_item.seats = f"{seat_3.seat_number}, {seat_4.seat_number}"
        return_order_item.save()

        # Try cancelling the order
        url = reverse_lazy("orders:order_cancel", args=[str(order.id)])
        self.client.post(url)

        seat_1.refresh_from_db()
        seat_2.refresh_from_db()
        seat_3.refresh_from_db()
        seat_4.refresh_from_db()

        # Verify that the seats are available again
        self.assertEqual(seat_1.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_2.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_3.seat_status, Seat.AVAILABLE)
        self.assertEqual(seat_4.seat_status, Seat.AVAILABLE)
