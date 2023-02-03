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

    trip = get_object_or_404(Trip, id=trip_id)

    # TODO: Veer You might NOT want to add booked seats to session
    # May be pass it as a fresh context on order page
    # or better expose and endpoint in trips app that provides booked seats for a trip :)
    # If we keep in a session data will be obsolete soon and wrong seat can be booked

    request.session["booked_seats"] = trip.get_booked_seats()  # <-- don't do this
    quantity = int(request.session["q"]["num_of_passengers"])

    logger.info(
        "veer inside cart_add(💋)... trip_id: %s quantity: %s" % (trip_id, quantity)
    )

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

    return redirect("cart:cart_detail")


def cart_detail(request):
    """
    Detail view to show all the contents in a cart.
    """

    logger.info("veer inside cart_detail(✍️)...")

    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})
