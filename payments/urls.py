from django.urls import path


app_name = "payments"


urlpatterns = [
    path('', views.PaymentOptionsView.as_view(), name="options"),
]