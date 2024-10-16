import uuid
from http import HTTPStatus

from django.conf import settings
from django.contrib.messages import get_messages
from django.http.response import HttpResponseRedirect
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from cart.cart import Cart
from companies.factories import CompanyFactory
from orders.factories import OrderFactory, OrderItemFactory
from orders.forms import OrderForm, PassengerForm
from orders.models import Order, OrderItem, Passenger
from orders.views import OrderCheckInView, OrderCreateView, order_cancel
from pages.views import HomePageView
from payments.views import PaymentView
from trips.factories import (
    LocationFactory,
    PriceFactory,
    RouteWithStopsFactory,
    SeatFactory,
    TripTomorrowFactory,
)
from trips.models import Price, Seat, Trip
from users.factories import CompanyOwnerFactory, UserFactory


class OrderCreateTests(TestCase):
    """
    Test suite for the main and very complex order create view

    Remember veer anytime you try to access OrderCreate view you should have
    these two things
        - 1. A search query in session
        - 2. A trip(s) in cart
    """

    def setUp(self):
        self.url = reverse_lazy("orders:order_create")
        self.template_name = OrderCreateView.template_name

        # Create a route with price and stops
        self.route = RouteWithStopsFactory()
        self.origin = self.route.origin
        self.destination = self.route.destination
        self.price = PriceFactory(
            route=self.route,
            origin=self.origin,
            destination=self.destination,
            amount=70000,
            category=Price.SEMICAMA,
        )

        # add trip for that route
        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )

        # create search query + cart and add them to session since order view expects them
        num_passengers = 5

        self.q = {
            "trip_type": "one_way",
            "num_of_passengers": str(num_passengers),
            "origin": self.origin.name,
            "destination": self.destination.name,
            "departure": self.trip.departure.strftime("%d-%m-%Y"),
            "return": "",
        }

        self.cart = {
            str(self.trip.id): {
                "quantity": num_passengers,
                "price": str(self.price.amount),
                "origin": self.origin.name,
                "destination": self.destination.name,
            }
        }

        session = self.client.session
        session["q"] = self.q
        session["cart"] = self.cart

        session.save()

    def test_order_create_page_works_via_get(self):
        response = self.client.get(self.url, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTemplateUsed(response, self.template_name)
        self.assertTemplateNotUsed(response, HomePageView.template_name)

        self.assertNotContains(response, "Hi I should not be on this page!")
        self.assertContains(response, "csrfmiddlewaretoken")

        # Passenger form html
        self.assertContains(response, "Passenger 1")
        self.assertContains(response, "Passenger 2")
        self.assertContains(response, "Passenger 3")
        self.assertContains(response, "Passenger 4")
        self.assertContains(response, "Passenger 5")

        # Payer form html
        self.assertContains(response, "Your Contact Information")
        self.assertContains(response, "Order")

        # Trip summary html
        self.assertContains(response, "Trip Summary")
        self.assertContains(response, "Company")

        # Price summary html
        self.assertContains(response, "Fare Summary")

        self.assertContains(response, self.origin)
        self.assertContains(response, self.destination)

        self.assertContains(response, self.trip.company)

        self.assertIn("cart", response.context)

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
        # Act
        # first let's clear the session set in setup()
        session = self.client.session
        session.clear()
        session.save()

        self.assertNotIn("q", self.client.session)

        # Act
        # now hit the order create page directly
        response = self.client.get(self.url, follow=True)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse_lazy("pages:home"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), settings.SESSION_EXPIRED_MESSAGE)

    def test_order_page_redirects_to_home_if_cart_is_empty(self):
        # Arrange: we empty the session
        session = self.client.session
        session.clear()
        session.save()

        self.assertNotIn("cart", self.client.session)

        # Act: now hit the order create page directly
        response = self.client.get(self.url, follow=True)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse_lazy("pages:home"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), settings.SESSION_EXPIRED_MESSAGE)


class OrderCreatePostTests(TestCase):
    """
    Test suite to verify Order Creation.
    """

    def setUp(self):
        """Build the session data for each test"""

        self.num_of_passengers = 2
        self.url = reverse_lazy("orders:order_create")
        self.payments_url = reverse_lazy("payments:home")
        self.template_name = OrderCreateView.template_name
        self.redirect_template_name = PaymentView.template_name

        # Create a route with stops
        self.route = RouteWithStopsFactory()
        self.origin = self.route.origin
        self.destination = self.route.destination

        # Create a price between origin, destination pair for semicama category
        self.price = PriceFactory(
            route=self.route,
            origin=self.origin,
            destination=self.destination,
            category=Price.SEMICAMA,
        )
        # Create a trip on our route with 2 available seats
        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )
        SeatFactory.reset_sequence(1)
        SeatFactory.create_batch(size=2, trip=self.trip, seat_status=Seat.AVAILABLE)

        self.cart = {
            str(self.trip.id): {
                "quantity": self.num_of_passengers,
                "price": str(self.price.amount),
                "origin": self.origin.name,
                "destination": self.destination.name,
            }
        }

        self.q = {
            "trip_type": "one_way",
            "num_of_passengers": str(self.num_of_passengers),
            "origin": self.origin.name,
            "destination": self.destination.name,
            "departure": self.trip.departure.strftime("%d-%m-%Y"),
            "return": "",
        }

        self.data = self.build_form_data()

        session = self.client.session
        session["q"] = self.q
        session["cart"] = self.cart
        session.save()

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
            expected_url=self.payments_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, PaymentView.template_name)
        self.assertTemplateNotUsed(response, "pages/home.html")
        self.assertContains(response, "Payment")
        self.assertNotContains(response, "Hi I should not be on this page")
        self.assertIsInstance(response.context["order"], Order)

    def test_order_success_creates_order_correctly(self):
        # Make sure initially no orders are present
        self.assertEqual(Order.objects.count(), 0)

        # Act: Now send post data
        response = self.client.post(self.url, data=self.data, follow=True)

        # Assert: Verify that order is created and unpaid
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
        self.assertEqual(order_item.price, self.price.amount)
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

    def test_order_success_places_order_id_in_session(self):
        response = self.client.post(self.url, data=self.data, follow=True)

        order = Order.objects.first()
        session = self.client.session

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("order", session)
        self.assertEqual(session.get("order"), str(order.id))

    def test_order_validation_errors_for_invalid_post_data(self):
        self.skipTest("Please implement me 🥹")

    def test_expired_session_marks_seats_as_available_again(self):
        self.skipTest("Please implement me 🥹")

    def test_order_creation_for_invalid_seat_numbers_redirects_with_message(self):
        self.skipTest("Please implement me 🥹")

    def test_order_creation_for_invalid_trip_redirects_with_message(self):
        self.skipTest("Please implement me 🥹")

    def test_valid_coupon_is_applied_to_order_successfully(self):
        self.skipTest("Please implement me 🥹")


class OrderCancelTests(TestCase):
    """
    Test suite to cancel an order
    """

    def setUp(self):
        self.url = reverse_lazy("orders:order_cancel", args=[str(self.order.id)])
        self.warning_msg = settings.SESSION_EXPIRED_MESSAGE

        self.route = RouteWithStopsFactory()
        self.origin = self.route.origin
        self.destination = self.route.destination
        self.price = PriceFactory(
            route=self.route,
            origin=self.origin,
            destination=self.destination,
            amount=10,
        )

        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )

        SeatFactory.reset_sequence(1)
        SeatFactory.create_batch(size=2, trip=self.trip, status=Seat.AVAILABLE)

        self.order = OrderFactory(paid=False)
        self.order_item = OrderItemFactory(order=self.order, trip=self.trip, price=10)

        # Initialize session with search query
        self.q = {
            "trip_type": "one_way",
            "num_of_passengers": str(self.num_of_passengers),
            "origin": self.origin.name,
            "destination": self.destination.name,
            "departure": self.trip.departure.strftime("%d-%m-%Y"),
            "return": "",
        }

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


class OrderCheckInTests(TestCase):
    """
    Test suite for checking in an order item.
    """

    @classmethod
    def setUpTestData(cls):
        # Create an company with owner and a valid trip
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.trip = TripTomorrowFactory(company=cls.company)

        # Make an order, order_item for this trip
        cls.order = OrderFactory()
        cls.order_item_1 = OrderItemFactory(order=cls.order, trip=cls.trip)

        cls.url = cls.order_item_1.get_checkin_url()
        cls.template_name = "orders/checkin.html"
        cls.login_url = reverse_lazy("account_login")

    def test_order_checkin_url_resolves_order_checkin_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, OrderCheckInView.as_view().__name__)

    def test_company_owner_can_access_order_checkin(self):
        """
        The qr code use to checkin a passenger should be accessible only by
        the company owner or a superuser.
        """

        # Make the company owner login
        user = self.owner
        self.client.force_login(user)

        # Try accessing the url (typically via qr code a get request will be sent)
        response = self.client.get(self.url)

        # Assert user is correctly authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertNotContains(response, "Hi I should not be on this page!")

        self.assertContains(response, "Checkin")
        self.assertContains(response, self.company)
        self.assertEqual(self.company, response.context["company"])
        self.assertEqual(self.order_item_1, response.context["item"])
        self.assertIn("item", response.context)

    def test_order_checkin_view_is_not_accessible_by_logged_in_normal_public_user(
        self,
    ):
        # Make a normal user and authenticate him/her
        user = UserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_order_checkin_view_is_not_accessible_by_anonymous_user(self):
        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, redirect_url)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_order_checkin_view_is_not_accessible_by_another_company_owner(self):
        """
        Company B owner should not be able to checkin a passenger for Company A
        by scanning the QR
        """

        # Create another company owner and log her in
        user = CompanyOwnerFactory()
        self.client.force_login(user)

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)
