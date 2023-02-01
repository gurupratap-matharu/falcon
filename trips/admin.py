from django.contrib import admin

from orders.models import Passenger

from .models import Location, Seat, Trip


class PassengerInline(admin.TabularInline):
    model = Passenger
    fk_name = "trip"
    readonly_fields = (
        "first_name",
        "last_name",
        "nationality",
        "phone_number",
        "seat_number",
    )
    exclude = (
        "order",
        "document_type",
        "document_number",
        "birth_date",
        "gender",
    )
    extra = 0
    can_delete = False


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    can_delete = False
    classes = ("collapse",)


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
    list_editable = (("status"),)
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("origin", "destination", "company")
    date_hierarchy = "departure"
    inlines = [PassengerInline]
