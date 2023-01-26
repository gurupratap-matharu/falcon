from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.TripListView.as_view(), name="trip-list"),
    path("<uuid:id>/<slug:slug>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("search/", views.TripSearchView.as_view(), name="trip-search"),
]
