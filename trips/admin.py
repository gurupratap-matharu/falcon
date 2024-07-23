import logging
from datetime import date, timedelta
from typing import Any

from django.contrib import admin
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from trips.models import Seat

from .models import Location, Route, Stop, Trip

logger = logging.getLogger(__name__)

admin.site.site_header = "Kpiola 🚌"
admin.site.site_title = "Kpiola Admin Portal"
admin.site.index_title = "Welcome to Kpiola Admin Portal"


class FutureFilter(admin.SimpleListFilter):
    """A simple custom filter to toggle only future trips in the admin"""

    title = _("Time")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "departure"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ("7", _("Future 7 days")),
            ("30", _("Future 30 days")),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '7' or '30')
        # to decide how to filter the queryset.
        today = date.today()

        if self.value() == "7":
            next_week = today + timedelta(days=7)
            return queryset.filter(
                departure__gte=today, departure__lte=next_week
            ).order_by("departure")

        if self.value() == "30":
            next_month = today + timedelta(days=30)
            return queryset.filter(
                departure__gte=today, departure__lte=next_month
            ).order_by("departure")


class TripOrderInline(admin.TabularInline):
    model = Trip.orders.through
    extra = 0
    can_delete = False
    readonly_fields = (
        "trip",
        "order",
        "quantity",
        "price",
        "seats",
    )


class PassengerSeatInline(admin.TabularInline):
    model = Trip.passengers.through  # <- This is the Seat model
    extra = 0
    can_delete = False
    fields = ("seat_number", "passenger", "seat_status", "seat_type")
    readonly_fields = (
        "seat_number",
        # "seat_status",
        "passenger",
        "seat_type",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        """
        Veer here the queryset is basically trip.seats.all() or all the seats
        for a trip.
        We want to pull in all passenger info in one go for faster response.
        """

        qs = super().get_queryset(request)
        return qs.select_related("passenger")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "abbr",
        "city",
        "state",
        "postal_code",
        "country",
        "latitude",
        "longitude",
    )
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_per_page = 30


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "route",
        "origin",
        "destination",
        "departure",
        "arrival",
        "duration",
        "status",
        "mode",
        "availability",
    )
    list_filter = (FutureFilter, "departure", "status")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("origin", "destination", "company")
    date_hierarchy = "departure"
    inlines = [
        PassengerSeatInline,
        TripOrderInline,
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)

        # Fetch related foreign keys in one go
        qs = qs.select_related("route", "origin", "destination", "company")

        # Annotate availability for all trips in  one go
        _availability = Count("seats", filter=Q(seats__seat_status=Seat.AVAILABLE))
        qs = qs.annotate(_availability=_availability)

        return qs

    def availability(self, obj):
        return obj._availability


class StopInline(admin.TabularInline):
    model = Stop
    list_display = ("order", "name", "arrival", "departure")
    autocomplete_fields = ("name",)
    extra = 1

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        qs = qs.select_related("route", "name")
        return qs


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "category",
        "origin",
        "destination",
        "active",
        "trips",
        "price_grid",
    )
    list_filter = ("active",)
    raw_id_fields = ("company", "origin", "destination")
    autocomplete_fields = ("origin", "destination")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (StopInline,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        qs = qs.select_related("company", "origin", "destination")
        return qs

    def trips(self, obj):
        """Link to our custom admin view"""

        url = reverse_lazy("trips:admin-route-detail", kwargs={"route_id": obj.id})
        html = format_html('<a href="{}">View</a>', url)

        return html

    @admin.display(description="Price Grid")
    def price_grid(self, obj):
        """Custom view to edit the price grid for a route"""

        url = reverse_lazy("trips:price-grid", kwargs={"route_id": obj.id})
        html = format_html('<a href="{}">View</a>', url)

        return html
