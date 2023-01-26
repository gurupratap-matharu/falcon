import logging
from typing import Any, Dict

from django.shortcuts import redirect
from django.views.generic import TemplateView, View

from .cart import Cart

logger = logging.getLogger(__name__)


class CartAddView(View):
    """
    Generic view to add a trip to the cart. Does not render a template
    """

    def post(self, request):
        cart = Cart(request)
        logger.info("veer inside cart post method")
        logger.info("request.post = %s" % request.POST)
        logger.info("cart = %s" % cart)

        return redirect("cart:cart-detail")


class CartDetailView(TemplateView):
    """
    Detail view to show all the contents in a cart.
    """

    template_name = "cart/cart_detail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        cart = Cart(self.request)
        context["cart"] = cart

        return context
