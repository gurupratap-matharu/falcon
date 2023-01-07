from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.TripSearchView.as_view(), name="trip-search"),
]
