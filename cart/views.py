import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from trips.models import Trip

from .cart import Cart

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def cart_add(request, trip_id=None):
    """
    Add a trip to the cart. Does not render a template
    """

    logger.info("veer inside cart_add(💋)... trip_id: %s", trip_id)

    trip = get_object_or_404(Trip, id=trip_id)

    cart = Cart(request)
    cart.add(trip=trip, quantity=1)  # TODO: fix quantity

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, trip_id):
    """
    Remove a trip to the cart. Does not render a template
    """

    logger.info("veer inside cart_remove(🎲)... trip_id: %s", trip_id)

    trip = get_object_or_404(Trip, id=trip_id)

    cart = Cart(request)
    cart.remove(trip)

    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    Detail view to show all the contents in a cart.
    """

    logger.info("veer inside cart_detail(✍️)...")

    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})
