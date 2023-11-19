from django.urls import path

from .views import LocationDetailView, LocationListView

app_name = "locations"

urlpatterns = [
    path("<slug:slug>/", LocationDetailView.as_view(), name="location-detail"),
    path("", LocationListView.as_view(), name="location-list"),
]
