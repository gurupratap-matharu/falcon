from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from cart.views import cart_detail, cart_remove
from coupons.forms import CouponApplyForm
from trips.factories import TripFactory
from trips.models import Trip


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

    def test_adding_more_than_two_trips_to_cart_redirects_with_message(self):
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

        # create two trips and add them to cart
        trip_1, trip_2, trip_3 = TripFactory.create_batch(size=3)

        # add the two trips to the cart as well
        _ = self.client.post(trip_1.get_add_to_cart_url())
        _ = self.client.post(trip_2.get_add_to_cart_url())

        # adding the third trip should redirect with message

        response = self.client.post(trip_3.get_add_to_cart_url())
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, reverse_lazy("cart:cart_detail"), HTTPStatus.FOUND
        )

        messages = list(get_messages(response.wsgi_request))
        trips_exceeded_msg = "You can add a maximum of two trips to your cart 🛒"

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), trips_exceeded_msg)

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


class CartRemoveTests(TestCase):
    """Test suite for cart remove view"""

    def setUp(self):
        self.trip = TripFactory()
        self.url = reverse_lazy("cart:cart_remove", args=[str(self.trip.id)])
        self.success_msg = "Item successfully removed from the cart. ✅"

    def test_cart_remove_only_accepts_post_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_cart_remove_url_resolves_cart_remove_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, cart_remove.__name__)

    def test_cart_remove_for_invalid_trip_throws_404_not_found(self):
        """
        We remove the trip from the DB so it does not exists and then
        try to access the view. This should throw 404 Not found
        """

        Trip.objects.all().delete()
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_cart_remove_redirects_to_cart_detail(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, reverse_lazy("cart:cart_detail"), HTTPStatus.FOUND
        )

    def test_cart_remove_redirects_with_success_message(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, reverse_lazy("cart:cart_detail"), HTTPStatus.FOUND
        )
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), self.success_msg)
