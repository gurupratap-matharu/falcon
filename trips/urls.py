from django.urls import path

from .views import (
    AdminRouteDetailView,
    PriceGridView,
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
    # remove this one
    path(
        "routes/<uuid:route_id>/price-grid/", PriceGridView.as_view(), name="price-grid"
    ),
    # Custom admin urls
    path(
        "admin/routes/<uuid:route_id>/",
        AdminRouteDetailView.as_view(),
        name="admin-route-detail",
    ),
]
