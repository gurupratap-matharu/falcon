from django.urls import path

app_name = "trips"

from . import views

url_patterns = [
    path("", views.TripSearchView.as_view(), name="trip-search"),
]
