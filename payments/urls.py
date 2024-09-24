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
    path("mercadopago/success/", views.mercadopago_success, name="mercadopago_success"),
    path(
        "webhooks/stripe/zoTcqmbblJYYLdyXn6sVyatEh3a3F2ZF/",
        views.stripe_webhook,
        name="stripe-webhook",
    ),
    path(
        "webhooks/mercadopago/drSndwy4YXkO15Zx1gABbbspSpxOasfx/",
        views.mercadopago_webhook,
        name="mercadopago-webhook",
    ),
    path("modo/", views.ModoView.as_view(), name="modo"),
]
