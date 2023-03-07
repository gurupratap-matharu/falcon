from django.urls import include, path

from trips.urls import trip_crud_patterns

from . import views

app_name = "companies"

urlpatterns = [
    # Public Views
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("<slug:slug>/", views.CompanyDetailView.as_view(), name="company_detail"),
    # Company Admin Views
    path("<slug:slug>/admin/", views.CompanyDashboardView.as_view(), name="dashboard"),
    path("<slug:slug>/admin/trips/", include(trip_crud_patterns)),
]
