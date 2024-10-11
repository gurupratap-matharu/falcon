import pdb
from http import HTTPStatus

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from cart.views import cart_detail, cart_remove
from coupons.forms import CouponApplyForm
from trips.factories import (
    PriceFactory,
    RouteWithStopsFactory,
    TripFactory,
    TripTomorrowFactory,
)
from trips.models import Price, Trip


class CartDetailViewTests(TestCase):
    """Test suite for cart detail view"""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse_lazy("cart:cart_detail")
        cls.template_name = "cart/cart_detail.html"
        cls.base_template = "layouts/base-app.html"
        cls.nav_template = "includes/navigation-light.html"

    def setUp(self):
        self.num_passengers = 5
        self.route = RouteWithStopsFactory()
        self.origin = self.route.origin
        self.destination = self.route.destination
        self.price = PriceFactory(
            route=self.route,
            origin=self.origin,
            destination=self.destination,
            category=Price.SEMICAMA,
        )
        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )

        # Create search query and add to session
        self.q = {
            "trip_type": "one_way",
            "num_of_passengers": str(self.num_passengers),
            "origin": self.origin.name,
            "destination": self.destination.name,
            "departure": self.trip.departure.strftime("%d-%m-%Y"),
            "return": "",
        }
        session = self.client.session
        session["q"] = self.q
        session.save()

    def test_cart_detail_url_resolves_cart_detail_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, cart_detail.__name__)

    def test_accepts_only_get(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_redirects_for_no_query_in_session(self):
        # Arrange - remove the search query we set in setup method
        session = self.client.session
        session.clear()
        session.save()

        self.assertNotIn("q", session)
        self.assertNotIn("q", self.client.session)

        # Act
        response = self.client.get(self.url, follow=True)

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertRedirects(
            response,
            reverse_lazy("pages:home"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
        # check alert message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), settings.SESSION_EXPIRED_MESSAGE)

    def test_cart_detail_view_for_empty_cart(self):
        # Arrange
        # In setup we have not added cart to session. So its empty

        # Act
        response = self.client.get(self.url)

        # Assert: statuscodes
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert: templates
        self.assertTemplateUsed(response, self.template_name)
        self.assertTemplateUsed(response, self.base_template)
        self.assertTemplateUsed(response, self.nav_template)

        # Assert: text
        self.assertContains(response, "Your Cart")
        self.assertContains(response, "Cart is Empty 🛒")
        self.assertContains(response, "Keep exploring")

        self.assertNotContains(response, "Checkout")
        self.assertNotContains(response, "I have a coupon")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert: context
        self.assertIsInstance(response.context["coupon_apply_form"], CouponApplyForm)
        self.assertEqual(response.context["origin"], self.origin)
        self.assertEqual(response.context["destination"], self.destination)

    def test_cart_detail_view_for_item_in_cart(self):
        # Arrange
        # We'll add the cart to the session manually
        cart = {
            str(self.trip.id): {
                "quantity": self.num_passengers,
                "price": str(self.price.amount),
                "origin": self.origin.name,
                "destination": self.destination.name,
            }
        }
        session = self.client.session
        session["cart"] = cart
        session.save()

        # In setup we have not added cart to session. So its empty

        # Act
        response = self.client.get(self.url)

        # Assert: statuscodes
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert: templates
        self.assertTemplateUsed(response, self.template_name)
        self.assertTemplateUsed(response, self.base_template)
        self.assertTemplateUsed(response, self.nav_template)

        # Assert: text
        self.assertContains(response, "Your Cart")
        self.assertContains(response, "Checkout")
        self.assertContains(response, "I have a coupon")
        self.assertContains(response, self.route.company)
        self.assertContains(response, self.origin)
        self.assertContains(response, self.destination)

        self.assertNotContains(response, "Cart is Empty 🛒")
        self.assertNotContains(response, "Keep exploring")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert: context
        self.assertIsInstance(response.context["coupon_apply_form"], CouponApplyForm)
        self.assertEqual(response.context["origin"], self.origin)
        self.assertEqual(response.context["destination"], self.destination)


class CartAddTests(TestCase):
    """Test suite to verify adding a trip to cart works"""

    def setUp(self):
        self.num_passengers = 5
        self.route = RouteWithStopsFactory()
        self.origin = self.route.origin
        self.destination = self.route.destination
        self.price = PriceFactory(
            route=self.route,
            origin=self.origin,
            destination=self.destination,
            category=Price.SEMICAMA,
        )
        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )
        self.url = self.trip.get_add_to_cart_url()
        self.q = {
            "trip_type": "one_way",
            "num_of_passengers": str(self.num_passengers),
            "origin": self.origin.name,
            "destination": self.destination.name,
            "departure": self.trip.departure.strftime("%d-%m-%Y"),
            "return": "",
        }

    def test_add_to_cart_only_accepts_post_request(self):
        response = self.client.get(self.url)  # hit GET request
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_with_no_query_in_session_redirects(self):
        # Arrange: session is already empty
        self.assertNotIn("q", self.client.session)

        # Act: try to add the trip to cart with post
        response = self.client.post(self.url, follow=True)

        # Assert
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertRedirects(
            response,
            reverse_lazy("pages:home"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
        # check alert message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), settings.SESSION_EXPIRED_MESSAGE)

    def test_adding_a_trip_to_cart_works(self):
        # Arrange: add the search query to session

        session = self.client.session
        session["q"] = self.q
        session.save()

        self.assertIn("q", self.client.session)
        self.assertNotIn("cart", self.client.session)

        # Act: add the trip to cart via post
        response = self.client.post(self.url, follow=True)

        # Assert: cart is in session now and is correct
        self.assertIn("cart", self.client.session)
        cart = self.client.session["cart"]
        actual = cart[str(self.trip.id)]
        expected = {
            "quantity": self.num_passengers,
            "price": str(self.price.amount),
            "origin": self.origin.name,
            "destination": self.destination.name,
        }
        self.assertDictEqual(actual, expected)

        # Assert: user redirected to order page
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse_lazy("orders:order_create"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )
        self.assertTemplateUsed(response, "orders/order_form.html")
        self.assertTemplateNotUsed(response, "pages/home.html")

    def test_adding_more_than_one_trip_to_cart_redirects_with_message(self):
        # Arrange: add query to session
        session = self.client.session
        session["q"] = self.q
        session.save()

        self.assertIn("q", self.client.session)
        self.assertNotIn("cart", self.client.session)

        # create an extra trip
        another_trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )

        # add our default trip to cart
        _ = self.client.post(self.trip.get_add_to_cart_url())
        self.assertIn("cart", self.client.session)
        self.assertIsNotNone(self.client.session["cart"])

        # adding the second trip should redirect with message
        response = self.client.post(another_trip.get_add_to_cart_url(), follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse_lazy("cart:cart_detail"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        messages = list(get_messages(response.wsgi_request))
        trips_exceeded_msg = "You can add a maximum of one trip to your cart."

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), trips_exceeded_msg)


class CartRemoveTests(TestCase):
    """Test suite for cart remove view"""

    def setUp(self):
        self.num_passengers = 5
        self.route = RouteWithStopsFactory()
        self.origin = self.route.origin
        self.destination = self.route.destination
        self.price = PriceFactory(
            route=self.route,
            origin=self.origin,
            destination=self.destination,
            category=Price.SEMICAMA,
        )
        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )
        self.url = reverse_lazy("cart:cart_remove", args=[str(self.trip.id)])
        self.success_msg = "Item successfully removed from the cart. ✅"
        self.q = {
            "trip_type": "one_way",
            "num_of_passengers": str(self.num_passengers),
            "origin": self.origin.name,
            "destination": self.destination.name,
            "departure": self.trip.departure.strftime("%d-%m-%Y"),
            "return": "",
        }
        self.cart = {
            str(self.trip.id): {
                "quantity": self.num_passengers,
                "price": str(self.price.amount),
                "origin": self.origin.name,
                "destination": self.destination.name,
            }
        }

        # add cart to session for all tests
        session = self.client.session
        session["q"] = self.q
        session["cart"] = self.cart
        session.save()

    def test_cart_remove_only_accepts_post_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_cart_remove_url_resolves_cart_remove_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, cart_remove.__name__)

    def test_cart_remove_for_invalid_trip_throws_404_not_found(self):
        # Arrange: we try to remove a trip that does not exists

        Trip.objects.all().delete()
        response = self.client.post(self.url, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_cart_remove_redirects_to_cart_detail_with_message(self):
        response = self.client.post(self.url, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse_lazy("cart:cart_detail"),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        self.assertTemplateUsed(response, "cart/cart_detail.html")

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), self.success_msg)
