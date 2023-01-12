from django.urls import path

from . import views

app_name = "payments"


urlpatterns = [
    path("", views.PaymentView.as_view(), name="home"),
    path("success/", views.PaymentSuccessView.as_view(), name="success"),
    path("fail/", views.PaymentFailView.as_view(), name="fail"),
    path("canceled/", views.PaymentCanceledView.as_view(), name="canceled"),
]
