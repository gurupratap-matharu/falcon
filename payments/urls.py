from django.urls import path

from . import views

app_name = "payments"


urlpatterns = [
    path("", views.PaymentView.as_view(), name="home"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("success/", views.PaymentSuccessView.as_view(), name="success"),
    path("pending/", views.PaymentPendingView.as_view(), name="pending"),
    path("fail/", views.PaymentFailView.as_view(), name="fail"),
    path("cancel/", views.PaymentCancelView.as_view(), name="cancel"),
    path(
        "mercadopago/success/", views.mercadopago_success, name="mercadopago_success"
    ),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe-webhook"),
    path(
        "webhooks/mercadopago/", views.mercadopago_webhook, name="mercadopago_webhook"
    ),
]
