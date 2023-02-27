import logging
import pdb
from decimal import Decimal

from django.conf import settings

from coupons.models import Coupon
from trips.models import Trip

logger = logging.getLogger(__name__)


class CartException(Exception):
    pass


class Cart:
    def __init__(self, request):
        """
        Initialize a cart.
        """

        self.session = request.session

        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart
        self.coupon_id = self.session.get("coupon_id")

    @property
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass

        return None

    def get_discount(self):
        """Calculate the discount applied on the total cart by a valid coupon (if any)"""

        if self.coupon:
            return (self.coupon.discount / Decimal(100)) * self.get_total_price()

        return Decimal(0)

    def get_total_price_after_discount(self):
        """Calculate the final price after applying coupon discount (if any)"""
        return self.get_total_price() - self.get_discount()

    def add(self, trip, quantity=1, override_quantity=False):
        """
        Add a trip to the cart or update its quantity.
        """

        # do not allow to add more than two trips
        if len(self.cart) == 2:
            raise CartException("Cannot add more than two trips to cart!")

        logger.info("adding to cart... trip: %s quantity: %s" % (trip, quantity))

        trip_id = str(trip.id)

        if trip_id not in self.cart:
            self.cart[trip_id] = {"quantity": 0, "price": str(trip.price)}

        if override_quantity:
            self.cart[trip_id]["quantity"] = quantity
        else:
            self.cart[trip_id]["quantity"] += quantity

        self.save()

    def remove(self, trip):
        """
        Remove a trip from the cart.
        """

        trip_id = str(trip.id)

        if trip_id in self.cart:
            del self.cart[trip_id]
            self.save()

    def save(self):
        """
        Marks the session as `modified` to make sure it gets saved.
        """

        logger.info("saving the cart...")
        self.session.modified = True

    def clear(self):
        """
        Removes the cart from the session
        """

        logger.info("clearing the cart...")

        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_total_price(self):
        """
        Calculate the total price across all trips and their quantities
        """

        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    def to_dict(self):
        """Builds a dict which is JSON serializable"""

        return [
            {
                "id": x["trip"].id,
                "quantity": x["quantity"],
                "price": x["price"],
                "booked_seats": x["trip"].get_booked_seats(),
            }
            for x in self
        ]

    def __iter__(self):
        """
        Iterate over the items in the cart and get the trips from the database.
        """

        trip_ids = self.cart.keys()

        # Get all the trip objects from DB and add them to the cart
        trips = Trip.objects.filter(id__in=trip_ids)
        cart = self.cart.copy()

        for trip in trips:
            cart[str(trip.id)]["trip"] = trip

        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        """
        Count all the items in the cart.
        """

        return sum(item["quantity"] for item in self.cart.values())

    def __repr__(self):

        logger.info("printing cart...")

        return "\n".join(
            [
                f"Trip: {k} Quantity: {v.get('quantity')} Price: {v.get('price')}"
                for k, v in self.cart.items()
            ]
        )
