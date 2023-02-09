import logging
from typing import Any, Dict

from django.forms import modelformset_factory
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from cart.cart import Cart

from .forms import OrderForm, PassengerForm
from .models import OrderItem, Passenger

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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        extra = int(self.request.session["q"]["num_of_passengers"])

        PassengerFormset = modelformset_factory(
            model=Passenger, form=PassengerForm, extra=extra
        )

        # TODO: Add passenger data to session and initialize formset with it
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
                seat_numbers = [s.strip() for s in seat_numbers.split(",")]

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

            # 6. redirect to payment

            self.request.session["order"] = str(order.id)

            return response

        else:
            return super().form_invalid(form)


"""
OrderConfirmedView()

This view is triggered when we get a webhook notification that an order is paid.
Generally I think this should be instantaneous in most cases before we show the
success url page. But we have to try it out.

            # Basically veer we need to do the following things here
            # 1. extract the order + order_items object from the DB
            # 2. confirm the seats for each order item with their respective trips
            # 3. when successful generate a pdf of the ticket
            # 4. shoot an email to the payer with pdf attached
            # 5. route to final success kind of page to download the ticket + ical
            # 6. prompt to book return ticket if this was one way else show some recommendations(not part of mvp)

"""
