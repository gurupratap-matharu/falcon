from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse_lazy

from cart.cart import Cart, CartException
from coupons.factories import CouponFactory
from trips.factories import (
    PriceFactory,
    RouteWithStopsFactory,
    TripFactory,
    TripTomorrowFactory,
)
from trips.models import Price, Trip


class SessionDict(dict):
    """Dummy session dict to be attached to request factory"""

    modified = False


class CartTests(TestCase):
    """
    Test Suite for the main cart class and all its methods.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get(reverse_lazy("cart:cart_detail"))
        self.num_passengers = 5

        # Create a route with stops and price between those stops
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

        # Create a trip running tommorow for that route
        self.trip = TripTomorrowFactory(
            route=self.route, status=Trip.ACTIVE, category=Trip.SEMICAMA
        )

        # Add a coupon to the mix
        self.coupon = CouponFactory()

        # Create cart object
        self.cart = {
            str(self.trip.id): {
                "quantity": self.num_passengers,
                "price": str(self.price.amount),
                "origin": self.origin.name,
                "destination": self.destination.name,
            }
        }

        # Add cart and coupon to session
        self.request.session = SessionDict()
        self.request.session["cart"] = self.cart
        self.request.session["coupon_id"] = str(self.coupon.id)

    def test_cart_is_initialized_correctly_for_empty_session(self):
        self.request.session.clear()
        cart = Cart(self.request)

        self.assertEqual(self.request.session["cart"], {})
        self.assertEqual(cart.cart, {})

    def test_existing_cart_in_session_is_correctly_parsed(self):
        # aliasing for simplicity
        request = self.request
        session = self.request.session

        # Act: instantiate the cart
        cart = Cart(request)

        # Assert: cart object has the session cart and coupon
        self.assertEqual(cart.cart, session["cart"])
        self.assertEqual(cart.coupon_id, session["coupon_id"])

    def test_cart_coupon_property(self):
        cart = Cart(self.request)

        self.assertEqual(cart.coupon, self.coupon)
        self.assertEqual(cart.coupon_id, str(self.coupon.id))

    def test_cart_discount_is_correctly_calculated_from_valid_coupon(self):
        cart = Cart(self.request)

        discount = self.coupon.discount
        actual = cart.get_discount()
        expected = (discount / Decimal(100)) * cart.get_total_price()  # type:ignore

        self.assertEqual(actual, expected)

    def test_cart_discount_is_zero_for_empty_coupon(self):
        """
        Remove the coupon_id from the session first and check the discount
        """
        del self.request.session["coupon_id"]

        cart = Cart(self.request)

        self.assertIsNone(cart.coupon_id)
        self.assertIsNone(cart.coupon)

        discount = cart.get_discount()
        self.assertEqual(Decimal(0), discount)

    def test_cart_discount_is_zero_for_invalid_coupon(self):
        self.request.session["coupon_id"] = "1234"  # invalid coupon id

        cart = Cart(self.request)

        self.assertIsNone(cart.coupon)

        discount = cart.get_discount()
        self.assertEqual(Decimal(0), discount)

    def test_adding_a_trip_to_cart_works(self):
        """
        We start with an empty session and add a trip later
        """

        # Arrange
        self.request.session.clear()

        trip = TripTomorrowFactory()
        origin = trip.origin
        destination = trip.destination
        price = 10
        qty = 5

        trip_id = str(trip.id)

        cart = Cart(self.request)
        # Act
        cart.add(
            trip=trip, origin=origin, destination=destination, price=price, quantity=qty
        )

        # Assert
        expected = {
            "quantity": qty,
            "price": str(price),
            "origin": origin.name,
            "destination": destination.name,
        }
        self.assertDictEqual(cart.cart[trip_id], expected)

    def test_adding_more_than_one_trip_to_cart_raises_exception(self):
        # The cart already has one trip added in setup method
        # Verify: cart has one trip
        cart = Cart(self.request)
        self.assertEqual(len(cart.cart), 1)

        # Adding another one should raise exception
        another_trip = TripTomorrowFactory()
        origin = another_trip.origin
        destination = another_trip.destination

        # Act & Assert
        with self.assertRaises(CartException):
            cart.add(
                trip=another_trip, origin=origin, destination=destination, price=10
            )

        # Assert: cart still has only one trip with 2 passengers
        self.assertEqual(len(cart.cart), 1)

    def test_user_can_add_maximum_one_trips_to_cart(self):
        # Arrange
        cart = Cart(self.request)
        # Cart already has one trip. Let's try adding another one
        trip = TripTomorrowFactory()

        # Act and Assert
        with self.assertRaises(CartException):
            cart.add(
                trip=trip,
                origin=trip.origin,
                destination=trip.destination,
                price=10,
                override_quantity=True,
            )

    def test_removing_an_existing_trip_from_cart_works(self):
        """
        Clear the session and create a trip.
        Add it to cart and verify all ok
        Remove the trip from cart and make sure it works.
        """

        # Arrange

        self.request.session.clear()

        trip = TripTomorrowFactory()
        trip_id = str(trip.id)

        cart = Cart(self.request)

        # Act
        cart.add(
            trip=trip,
            origin=trip.origin,
            destination=trip.destination,
            price=10,
            quantity=2,
            override_quantity=True,
        )

        self.assertIn(trip_id, cart.cart)

        # now remove the trip and check its not in cart
        cart.remove(trip=trip)

        # Assert
        self.assertNotIn(trip, cart.cart)

    def test_removing_a_non_existing_trip_from_cart_has_no_effect(self):
        # Arrange
        cart = Cart(self.request)
        some_random_trip = TripFactory()  # 👈 this trip is not added to cart

        self.assertEqual(len(cart), self.num_passengers)
        self.assertEqual(len(cart.cart), 1)  # num of trips

        # Act
        cart.remove(trip=some_random_trip)

        # Assert: make sure removal has no effect
        self.assertEqual(len(cart), self.num_passengers)
        self.assertEqual(len(cart.cart), 1)  # num of trips

    def test_saving_a_cart_works(self):
        cart = Cart(self.request)
        self.assertFalse(cart.session.modified)

        cart.save()
        self.assertTrue(cart.session.modified)

    def test_clearing_a_cart_removes_all_trips_from_cart(self):
        # Arrange
        cart = Cart(self.request)

        self.assertEqual(len(cart), self.num_passengers)  # num of passengers
        self.assertEqual(len(cart.cart), 1)  # num of trips

        # Act
        cart.clear()

        # Assert
        self.assertNotIn("cart", cart.session)
        self.assertNotIn("cart", self.request.session)

        # We need to instantiate the cart again as the session itself was cleared
        cart = Cart(self.request)

        self.assertEqual(len(cart), 0)
        self.assertEqual(len(cart.cart), 0)

    def test_get_total_price_works_correctly(self):
        cart = Cart(self.request)

        expected = sum(
            Decimal(item["price"]) * item["quantity"] for item in cart.cart.values()
        )
        actual = cart.get_total_price()

        self.assertEqual(actual, expected)

    def test_get_total_price_after_discount_works_correctly(self):
        cart = Cart(self.request)

        actual = cart.get_total_price_after_discount()
        expected = cart.get_total_price() - cart.get_discount()

        self.assertEqual(actual, expected)

    def test_len_of_cart_is_correctly_calculated(self):
        cart = Cart(self.request)

        self.assertEqual(len(cart), self.num_passengers)
        self.assertEqual(len(cart.cart), 1)  # num of trips
