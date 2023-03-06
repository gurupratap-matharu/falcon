from django.urls import include, path

from . import views

app_name = "companies"

company_admin_patterns = [
    path("", views.CompanyDashboardView.as_view(), name="dashboard"),
    path("trips/", views.ManageTripListView.as_view(), name="manage_trip_list"),
    path("trips/create/", views.TripCreateView.as_view(), name="trip_create"),
    path("trips/<uuid:id>/update/", views.TripUpdateView.as_view(), name="trip_update"),
    path("trips/<uuid:id>/delete/", views.TripDeleteView.as_view(), name="trip_delete"),
]

urlpatterns = [
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("<slug:slug>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path("<slug:slug>/admin/", include(company_admin_patterns)),
]
