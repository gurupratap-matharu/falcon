import logging
from typing import Any, Dict

from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from cart.cart import Cart

from .forms import OrderForm, PassengerForm
from .models import Order, OrderItem, Passenger

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

        PassengerFormset = inlineformset_factory(
            parent_model=Order,
            model=Passenger,
            form=PassengerForm,
            extra=extra,
            can_delete=False,
        )

        context["formset"] = PassengerFormset(self.request.POST or None)
        context["cart"] = Cart(self.request)

        logger.info("OrderCreateView: request.POST: %s" % self.request.POST)
        logger.info("OrderCreateView: context: %s" % context)

        return context

    def form_valid(self, form) -> HttpResponse:
        logger.info("veer order form is valid(💋)")

        formset = self.get_context_data()["formset"]

        if formset.is_valid():
            logger.info("veer passenger formset.is_valid(💑) %s" % formset.is_valid())

            response = super().form_valid(form)  # <- this sets the self.object (order)
            order = self.object

            formset.instance = order  # <- Set order FK for all passengers
            # TODO: Yet to add trip to passengers
            passengers = formset.save()

            logger.info("veer created order(🗽) %s" % order)
            logger.info("veer created passengers(👨‍👩‍👧‍👦)%s" % passengers)

            cart = Cart(self.request)
            for item in cart:
                order_item = OrderItem.objects.create(
                    order=order,
                    trip=item["trip"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
                logger.info("veer created order_item(📝): %s", order_item)

            cart.clear()

            logger.info("veer cleared the cart(🛒)...")

            return response

        else:
            return super().form_invalid(form)
