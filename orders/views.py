import logging
from typing import Any, Dict

from django import http
from django.conf import settings
from django.contrib import messages
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView

from django_weasyprint import WeasyTemplateResponseMixin

from cart.cart import Cart
from companies.mixins import OwnerMixin

from .forms import OrderForm, PassengerForm
from .models import Order, OrderItem, Passenger

logger = logging.getLogger(__name__)


class OrderCreateView(CreateView):
    """
    View that allows a user to create an order and multiple passengers in one go using formsets.
    """

    form_class = OrderForm
    template_name = "orders/order_form.html"
    success_url = reverse_lazy("payments:home")
    redirect_message = "Your session has expired. Please search again 🙏"

    def get_initial(self):
        user = self.request.user
        initial = {"name": user.first_name, "email": user.email}
        logger.info("initial:%s" % initial)
        return initial

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

        logger.info("order form is valid...")

        cart = Cart(self.request)
        formset = self.get_formset()

        if not formset.is_valid():
            return super().form_invalid(form)

        logger.info("passenger formset is valid...")

        # Get the http response that this method has to return
        # this also sets the self.object (order)
        response = super().form_valid(form)

        # Create an order object thats saved to the DB
        order = self.object

        # Apply coupon to order if needed
        if cart.coupon:
            logger.info("attaching coupon %s..." % cart.coupon)
            order.coupon = cart.coupon
            order.discount = cart.coupon.discount
            order.save()

        # Create passenger objects
        passengers = formset.save()
        logger.info("passengers created %s..." % passengers)

        # Create and save order -> passenger m2m
        order.passengers.add(*passengers)
        order.save()

        for item in cart:
            trip = item["trip"]

            # Extract seat numbers from POST data and clean them
            seat_numbers = self.request.POST.get(f"seats{trip.id}", "")

            # Mark the seats for hold for each trip
            seats = trip.hold_seats(seat_numbers)

            logger.info("Trip: %s selected seats: %s" % (trip, seat_numbers))
            logger.info("seats held %s...", seats)

            # Create order item objects (order, trip, seatnos) combo
            order_item = OrderItem.objects.create(
                order=order,
                trip=trip,
                price=item["price"],
                quantity=item["quantity"],
                seats=seat_numbers,
            )

            logger.info("order_item %s...", order_item)

        cart.clear()

        # Save order.id in session so payments can access it
        order_id = str(order.id)
        self.request.session["order"] = order_id

        # TODO: Should we add any success message to request here?
        # Redirect to payment
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


class InvoiceView(DetailView):
    model = Order
    pk_url_kwarg = "order_id"
    template_name = "orders/invoice.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        order = self.object
        items = OrderItem.objects.filter(order=order).select_related("trip")
        item = items.first()
        trip = item.trip
        company = trip.company
        passengers = order.passengers.all()
        qr_url = f"{settings.BASE_URL}{item.get_checkin_url()}"

        context["order"] = order
        context["item"] = item
        context["trip"] = trip
        context["company"] = company
        context["code"] = str(order.id).split("-")[-1]
        context["trip_code"] = str(trip.id).split("-")[-1]
        context["passengers"] = passengers
        context["qr_url"] = qr_url

        return context


class InvoicePDFView(WeasyTemplateResponseMixin, InvoiceView):
    pass


class TicketView(DetailView):
    model = Order
    pk_url_kwarg = "order_id"
    template_name = "orders/ticket.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        item = order.items.first()
        trip = item.trip
        company = trip.company
        qr_url = f"{settings.BASE_URL}{item.get_checkin_url()}"
        logger.info("qr_url:%s" % qr_url)

        context["company"] = company
        context["order"] = order
        context["item"] = item
        context["trip"] = trip
        context["code"] = str(order.id).split("-")[-1]
        context["trip_code"] = str(trip.id).split("-")[-1]
        context["passengers"] = order.passengers.all()
        context["qr_url"] = qr_url

        return context


class TicketPDFView(WeasyTemplateResponseMixin, TicketView):
    pdf_attachment = False

    def get_pdf_filename(self):
        name = self.object.name.replace(" ", "-")
        return f"Tickets-{name}.pdf"


class OrderCheckInView(OwnerMixin, DetailView):
    """
    Veer this is a placeholder view that will checkin all the passengers in an order
    item. Typically this view will be triggered via scanning a QR code and a get request.

    Only the company owner or super user can access this. Some logic has to be implemented
    to checkin the actual passenger. For now a place holder to validate qr codes.
    """

    model = OrderItem
    template_name = "orders/checkin.html"
    context_object_name = "item"

    def get_object(self):
        order_item = get_object_or_404(
            OrderItem,
            pk=self.kwargs.get("orderitem_id"),
            order=self.kwargs.get("order_id"),
        )

        logger.info("checking in:%s" % order_item)
        return order_item
