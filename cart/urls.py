from django.urls import path

from .views import CartDetailView

app_name = "cart"

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart-detail"),
]
