import logging

from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from cart.cart import Cart

from .models import Order, OrderItem

logger = logging.getLogger(__name__)


class OrderView(TemplateView):
    template_name: str = "orders/order.html"


class OrderCreateView(CreateView):
    """
    Create an Order if a valid form is submitted.
    Also creates OrderItems for each item in the cart.
    """

    model = Order
    fields = ("name", "email", "residence")
    success_url = reverse_lazy("payments:home")

    def form_valid(self, form) -> HttpResponse:

        logger.info("veer order form is valid(💋)")

        order = form.save()
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
