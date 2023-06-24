from django.urls import path

from . import views

app_name = "trips"


urlpatterns = [
    # Public Endpoints
    path("", views.TripListView.as_view(), name="trip-list"),
    path("<uuid:id>/<slug:slug>/", views.TripDetailView.as_view(), name="trip_detail"),
    path("search/", views.TripSearchView.as_view(), name="trip-search"),
    path(
        "locations/<slug:slug>/",
        views.LocationDetailView.as_view(),
        name="location-detail",
    ),
    path("recurrence/", views.RecurrenceView.as_view(), name="recurrence"),
]
