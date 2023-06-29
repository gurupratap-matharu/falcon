import logging
from typing import Any, Dict

from django import http
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from cart.cart import Cart

from .drawers import burn_order_pdf, burn_ticket_pdf
from .forms import OrderForm, PassengerForm
from .models import Order, OrderItem, Passenger
from .services import order_created

logger = logging.getLogger(__name__)


class OrderCreateView(CreateView):
    """
    View that allows a user to create an order and multiple passengers in one got using formsets.
    """

    form_class = OrderForm
    template_name = "orders/order_form.html"
    success_url = reverse_lazy("payments:home")
    redirect_message = "Your session has expired. Please search again 🙏"

    def dispatch(
        self, request: http.HttpRequest, *args: Any, **kwargs: Any
    ) -> http.HttpResponse:
        """
        If session is empty then redirect user to home.
        """

        q = request.session.get("q")
        cart = request.session.get("cart")

        if not (q and cart):
            messages.info(request, self.redirect_message)
            return redirect("pages:home")

        return super().dispatch(request, *args, **kwargs)

    def get_formset(self):
        """
        Build and return a passenger formset
        # TODO: Try to add a typehint to this class.
        # See this: https://stackoverflow.com/questions/46007544/python-3-type-hint-for-a-factory-method-on-a-base-class-returning-a-child-class
        """

        q = self.request.session.get("q")
        extra = int(q.get("num_of_passengers", 0))

        data = self.request.POST or None
        queryset = Passenger.objects.none()

        PassengerFormset = modelformset_factory(
            model=Passenger, form=PassengerForm, extra=extra
        )

        formset = PassengerFormset(data=data, queryset=queryset)

        return formset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["cart"] = Cart(self.request)
        context["formset"] = self.get_formset()

        return context

    def form_valid(self, form) -> HttpResponse:
        """
        Order form is already validated at this point.
        Now we need to run logic to
            - validate and process formset
            - proceed to payment
        """

        logger.info("veer order form is valid(💋)...")

        cart = Cart(self.request)
        formset = self.get_formset()

        if not formset.is_valid():
            return super().form_invalid(form)

        logger.info("veer passenger formset.is_valid(💑)")

        # First get the http response that this method has to return
        # this also sets the self.object (order)
        response = super().form_valid(form)

        # 1. create an order object thats saved to the DB
        order = self.object

        # Apply coupon to order if needed
        if cart.coupon:
            logger.info("attaching coupon(🎟️) to order(🗽)...")
            order.coupon = cart.coupon
            order.discount = cart.coupon.discount
            order.save()

        logger.info("veer created order(🗽) %s" % order)

        # 2. create valid passenger objects
        passengers = formset.save()
        logger.info("veer created passengers(👨‍👩‍👧‍👦)%s" % passengers)

        # 3. create and save order -> passenger m2m
        order.passengers.add(*passengers)
        order.save()
        logger.info("veer order.passengers.all(): %s" % order.passengers.all())

        for item in cart:
            trip = item["trip"]

            # Extract seat numbers from POST data and clean them
            seat_numbers = self.request.POST.get(f"seats{trip.id}", "")

            # 4. Mark the seats for hold for each trip
            logger.info(
                "veer for trip: %s you selected seats: %s" % (trip, seat_numbers)
            )

            seats = trip.hold_seats(seat_numbers)

            logger.info("veer I've put on hold seats %s", seats)

            # 5. create order item objects (order, trip, seatnos) combo
            order_item = OrderItem.objects.create(
                order=order,
                trip=trip,
                price=item["price"],
                quantity=item["quantity"],
                seats=seat_numbers,
            )

            logger.info("veer created order_item(📝): %s", order_item)

        cart.clear()

        # 6. Save order.id in session so payments can access it
        order_id = str(order.id)
        self.request.session["order"] = order_id
        self.request.session.set_expiry(300)

        # 7. Send order creation email
        # TODO: run this async with celery
        order_created(order_id=order_id)

        # TODO: Should we add any success message to request here?
        # 8. Redirect to payment
        return response


@require_POST
@csrf_exempt
def order_cancel(request, order_id=None):
    """
    Use to mark an order's seats as `Available` again.
    Typically when a user created an order but made no payment during a session.

    In the DB the order is not deleted. This view does not render a template.
    """

    message = "Your session has expired. Please search again 🙏"

    cart = Cart(request)
    cart.clear()

    if "order" in request.session:
        del request.session["order"]
        logger.info("removed order from session...")

    order = get_object_or_404(Order, id=order_id)
    for item in order.items.all():
        trip, seat_numbers = item.trip, item.seats

        logger.info("trip:%s, seats:%s" % (trip, seat_numbers))
        trip.release_seats(seat_numbers=seat_numbers)

    logger.info("cancelled order:%s..." % order)

    messages.warning(request=request, message=message)

    return redirect("pages:home")


@staff_member_required
def admin_order_pdf(request, order_id):
    """
    Staff view used in admin interface to view the invoice of any order
    """
    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={order.name}.pdf"

    burn_order_pdf(target=response, order=order)

    return response


def ticket(request, order_id):
    """
    Simple view to see a preview of the final ticket render in html format
    """

    order = get_object_or_404(Order, id=order_id)
    context = {
        "order": order,
        "trip": order.trips.first(),  # type:ignore
        "passengers": order.passengers.all(),
    }
    return render(request, "orders/ticket.html", context)


def ticket_pdf(request, order_id):
    """Generate a PDF ticket for download"""

    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=tickets.pdf"

    burn_ticket_pdf(request=request, target=response, order=order)

    return response
