from django.contrib import admin

from .models import Location, Trip


class TripOrderInline(admin.TabularInline):
    model = Trip.orders.through
    extra = 0
    can_delete = False
    readonly_fields = (
        "order",
        "quantity",
        "price",
    )


class PassengerSeatInline(admin.TabularInline):
    model = Trip.passengers.through
    extra = 0
    can_delete = False
    readonly_fields = (
        "seat_number",
        "seat_status",
        "passenger",
        "seat_type",
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "abbr", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_editable = ("abbr",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """
    TODO
        - show Price in localized money format say ARS 13,252.00
        - Allow filter to remove all past trips
        - In Future: Show passengers in each trip
    """

    list_display = (
        "company",
        "origin",
        "destination",
        "departure",
        "arrival",
        "duration",
        "status",
        "mode",
        "seats_available",
    )
    list_filter = ("departure", "status")
    list_editable = ("status",)
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("origin", "destination", "company")
    date_hierarchy = "departure"
    inlines = [
        TripOrderInline,
        PassengerSeatInline,
    ]


admin.site.site_header = "Falcon Admin"
admin.site.site_title = "Falcon Admin Portal"
admin.site.index_title = "Welcome to Falcon Admin Portal"
