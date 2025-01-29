from django.urls import path

from .views import AdminRouteDetailView, TripDetailView, TripListView, TripSearchView

app_name = "trips"


urlpatterns = [
    # Public Endpoints
    path("", TripListView.as_view(), name="trip-list"),
    path("<uuid:id>/", TripDetailView.as_view(), name="trip-detail"),
    path("search/", TripSearchView.as_view(), name="trip-search"),
    # Custom admin urls
    path(
        "admin/routes/<uuid:route_id>/",
        AdminRouteDetailView.as_view(),
        name="admin-route-detail",
    ),
]
