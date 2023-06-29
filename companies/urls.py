from django.urls import include, path

from coupons import views as coupon_views
from trips import views as trip_views

from . import views

app_name = "companies"


company_admin_patterns = [
    # Private Company Admin Endpoints
    path("", views.CompanyDashboardView.as_view(), name="dashboard"),
    path("trips/", trip_views.CompanyTripListView.as_view(), name="trip-list"),
    path("trips/create/", trip_views.TripCreateView.as_view(), name="trip-create"),
    path(
        "trips/<uuid:id>/",
        trip_views.CompanyTripDetailView.as_view(),
        name="trip-detail",
    ),
    path(
        "trips/<uuid:id>/passengers/pdf/",
        trip_views.TripPassengerPdfView.as_view(),
        name="trip-passengers-pdf",
    ),
    path(
        "trips/<uuid:id>/update/",
        trip_views.TripUpdateView.as_view(),
        name="trip-update",
    ),
    path(
        "trips/<uuid:id>/recurrence/",
        trip_views.RecurrenceView.as_view(),
        name="trip-recurrence",
    ),
    path("coupons/", coupon_views.CouponListView.as_view(), name="coupon-list"),
]


urlpatterns = [
    # Public Views
    path("", views.CompanyListView.as_view(), name="company_list"),
    path("landing/", views.CompanyLandingView.as_view(), name="company-landing"),
    path("<slug:slug>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path("<slug:slug>/book/", views.CompanyBookView.as_view(), name="company-book"),
    #
    # Company Admin Views
    path("<slug:slug>/admin/", include(company_admin_patterns)),
]
