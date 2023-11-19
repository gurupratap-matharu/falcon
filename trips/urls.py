from django.urls import path

from .views import (
    LocationDetailView,
    LocationListView,
    TripDetailView,
    TripListView,
    TripSearchView,
)

app_name = "trips"


urlpatterns = [
    # Public Endpoints
    path("", TripListView.as_view(), name="trip-list"),
    path("<uuid:id>/<slug:slug>/", TripDetailView.as_view(), name="trip_detail"),
    path("search/", TripSearchView.as_view(), name="trip-search"),
    path(
        "locations/<slug:slug>/", LocationDetailView.as_view(), name="location-detail"
    ),
    path("locations/", LocationListView.as_view(), name="location-list"),
]
