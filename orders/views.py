import logging
from typing import Any, Dict

from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from cart.cart import Cart

from .forms import OrderForm, PassengerFormset
from .models import OrderItem

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

        context["cart"] = Cart(self.request)
        context["formset"] = PassengerFormset(self.request.POST or None)

        logger.info("OrderCreateView: request.POST: %s" % self.request.POST)
        logger.info("OrderCreateView: context: %s" % context)

        return context

    def form_valid(self, form) -> HttpResponse:

        logger.info("veer order form is valid(💋)")

        order = form.save()

        formset = self.get_context_data()["formset"]

        if formset.is_valid():
            logger.info("veer passenger 💑 formset is valid(💋)")
            formset.order = order
            formset.save()

        cart = Cart(self.request)
        for item in cart:
            order_item = OrderItem.objects.create(
                order=order,
                trip=item["trip"],
                price=item["price"],
                quantity=item["quantity"],
            )
            logger.info("veer (💋) created order_item: %s", order_item)

        cart.clear()

        logger.info("veer(💋) cleared the cart...")

        return super().form_valid(form)
