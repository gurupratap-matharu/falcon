from .cart import Cart


def cart(request):
    """Make the cart available in context of any template"""

    return {"cart": Cart(request)}
