import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from coupons.forms import CouponApplyForm
from trips.models import Location, Trip

from .cart import Cart, CartException

logger = logging.getLogger(__name__)


@require_POST
def cart_add(request, trip_id=None):
    """
    Add a trip to the cart. Does not render a template
    """

    trips_exceeded_msg = _("You can add a maximum of one trip to your cart.")

    if not request.session.get("q"):
        # No search query in session so redirect to search again
        messages.info(request, settings.SESSION_EXPIRED_MESSAGE)
        return redirect("pages:home")

    q = request.session["q"]

    trip = get_object_or_404(Trip, id=trip_id)

    quantity = int(q["num_of_passengers"])
    origin = get_object_or_404(Location, name__iexact=q["origin"])
    destination = get_object_or_404(Location, name__iexact=q["destination"])

    price = trip.get_price(origin, destination)

    logger.info(
        "adding to cart(🛒)... trip_id:%s quantity:%s price:%s"
        % (trip_id, quantity, price)
    )

    cart = Cart(request)

    try:
        cart.add(trip=trip, quantity=quantity, price=price)

    except CartException:
        messages.info(request, trips_exceeded_msg)
        return redirect("cart:cart_detail")

    return redirect("orders:order_create")


@require_POST
def cart_remove(request, trip_id):
    """
    Remove a trip to the cart. Does not render a template
    """

    trip = get_object_or_404(Trip, id=trip_id)

    cart = Cart(request)
    cart.remove(trip)

    messages.success(request, "Item successfully removed from the cart. ✅")

    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    Detail view to show all the contents in a cart.
    """
    cart = Cart(request)
    coupon_apply_form = CouponApplyForm()
    context = {"cart": cart, "coupon_apply_form": coupon_apply_form}

    return render(request, "cart/cart_detail.html", context)
