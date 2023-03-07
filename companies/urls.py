from django.urls import include, path

from trips import views as trip_views

from . import views

app_name = "companies"


company_admin_patterns = [
    # Private Company Admin Endpoints
    path("", views.CompanyDashboardView.as_view(), name="dashboard"),
    path("trips/create/", trip_views.TripCreateView.as_view(), name="trip_create"),
]

urlpatterns = [
    # Public Views
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("<slug:slug>/", views.CompanyDetailView.as_view(), name="company_detail"),
    #
    # Company Admin Views
    path("<slug:slug>/admin/", include(company_admin_patterns)),
]
