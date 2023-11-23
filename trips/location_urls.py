from django.urls import path

from .views import LocationDetailView, LocationListView

app_name = "locations"

urlpatterns = [
    path("<slug:slug>/", LocationDetailView.as_view(), name="location-detail"),
    path("", LocationListView.as_view(), name="location-list"),
    # nice to have
    # "/terminals?latitude=49.0000&longitude=2.55" <- find terminals closest to this lat lon
    # "<slug:slug>/destinations/?max=2" <- show all destinations (locations) from this location
]
