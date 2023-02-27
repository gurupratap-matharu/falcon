from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from cart.views import cart_add, cart_detail
from coupons.forms import CouponApplyForm
from trips.factories import TripFactory


class CartDetailViewTests(TestCase):
    """Test suite for cart detail"""

    url = reverse_lazy("cart:cart_detail")
    template_name = "cart/cart_detail.html"

    def test_cart_detail_view_works(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Cart")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_cart_detail_url_resolves_cart_detail_view(self):
        view = resolve(self.url)

        self.assertEqual(view.func.__name__, cart_detail.__name__)

    def test_cart_detail_renders_coupon_apply_form(self):
        response = self.client.get(self.url)
        form = response.context["coupon_apply_form"]

        self.assertIsInstance(form, CouponApplyForm)


class CartAddTests(TestCase):
    """Test suite to verify adding a trip to cart works"""

    def setUp(self):
        self.trip = TripFactory()
        self.url = self.trip.get_add_to_cart_url()  # type:ignore
        self.failure_msg = "Oops! Perhaps your session expired. Please search again."

    def test_add_to_cart_only_accepts_post_request(self):
        response = self.client.get(self.url)  # try GET
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_adding_a_trip_to_cart_works(self):
        # First we build a valid search query and add it to the session
        session = self.client.session
        session["q"] = {
            "trip_type": "one_way",
            "num_of_passengers": "2",
            "origin": "Alta Gracia",
            "destination": "Alvear",
            "departure": "06-03-2023",
            "return": "",
        }
        session.save()

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, reverse_lazy("orders:order_create"), HTTPStatus.FOUND
        )

    def test_adding_trip_to_cart_without_search_query_redirects_with_message(self):
        """
        In this case session has no search query i.e. no info about `num_of_passengers`
        So adding to cart should not work and redirect with message.
        """
        self.client.session.clear()
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), self.failure_msg)
