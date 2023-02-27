import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from coupons.forms import CouponApplyForm
from trips.models import Trip

from .cart import Cart

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def cart_add(request, trip_id=None):
    """
    Add a trip to the cart. Does not render a template
    """

    if not request.session.get("q"):
        # No search query in session so redirect to search again
        messages.warning(
            request, "Oops! Perhaps your session expired. Please search again."
        )
        return redirect("pages:home")

    trip = get_object_or_404(Trip, id=trip_id)
    quantity = int(request.session["q"]["num_of_passengers"])

    logger.info("adding to cart(🛒)... trip_id:%s quantity:%s" % (trip_id, quantity))

    cart = Cart(request)
    cart.add(trip=trip, quantity=quantity)

    return redirect("orders:order_create")


@require_POST
def cart_remove(request, trip_id):
    """
    Remove a trip to the cart. Does not render a template
    """

    logger.info("veer inside cart_remove(🎲)... trip_id: %s", trip_id)

    trip = get_object_or_404(Trip, id=trip_id)

    cart = Cart(request)
    cart.remove(trip)

    messages.success(request, "Item successfully removed from the cart. ✅")

    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    Detail view to show all the contents in a cart.
    """

    logger.info("veer inside cart_detail(✍️)...")

    cart = Cart(request)
    coupon_apply_form = CouponApplyForm()

    return render(
        request,
        "cart/cart_detail.html",
        {"cart": cart, "coupon_apply_form": coupon_apply_form},
    )
