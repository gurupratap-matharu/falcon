import logging
from typing import Any, Dict

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from cart.cart import Cart

from .drawers import burn_order_pdf
from .forms import OrderForm, PassengerForm
from .models import Order, OrderItem, Passenger
from .services import order_created

logger = logging.getLogger(__name__)


class OrderView(TemplateView):
    template_name: str = "orders/order.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["cart"] = Cart(self.request)

        return context


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

        if "q" not in request.session:
            messages.info(request, self.redirect_message)
            return redirect("pages:home")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        extra = int(self.request.session["q"]["num_of_passengers"])

        PassengerFormset = modelformset_factory(
            model=Passenger, form=PassengerForm, extra=extra
        )

        context["formset"] = PassengerFormset(
            data=self.request.POST or None, queryset=Passenger.objects.none()
        )
        context["cart"] = Cart(self.request)

        logger.info("OrderCreateView: request.POST: %s" % self.request.POST)
        logger.info("OrderCreateView: context: %s" % context)

        return context

    def form_valid(self, form) -> HttpResponse:
        logger.info("veer order form is valid(💋)")

        context = self.get_context_data()
        cart, formset = context["cart"], context["formset"]

        if formset.is_valid():

            logger.info("veer passenger formset.is_valid(💑) %s" % formset.is_valid())
            # Basically veer we need to do the following things here

            # 1. create an order object thats saved to the DB
            response = super().form_valid(form)  # <- this sets the self.object (order)
            order = self.object  # type:ignore
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

                logger.info("veer I've put on hold %s number of seats(💺)", seats)

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

            logger.info("veer cleared the cart(🛒)...")

            # 6. Save order.id in session so payments can access it
            order_id = str(order.id)
            self.request.session["order"] = order_id
            self.request.session["pdf_url"] = order.get_pdf_url()

            # 7. Send order creation email
            order_created(order_id=order.id)

            # 8. Redirect to payment
            return response

        else:
            return super().form_invalid(form)


@staff_member_required
def admin_order_pdf(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={order.name}.pdf"

    burn_order_pdf(on=response, order=order)

    return response
