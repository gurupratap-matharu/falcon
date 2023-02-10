from django.contrib import admin

from trips.admin import TripOrderInline

from .models import Order, OrderItem, Passenger


class OrderPassengerInline(admin.TabularInline):
    model = Order.passengers.through
    readonly_fields = (
        "order",
        "passenger",
    )
    extra = 0
    can_delete = False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "trip", "quantity", "price", "seats")
    readonly_fields = ("order", "trip", "price", "seats", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "residence", "paid", "created_on")
    exclude = ("passengers",)
    list_filter = ("paid", "created_on", "updated_on")
    inlines = [
        OrderPassengerInline,
        TripOrderInline,
    ]


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document_type",
        "document_number",
        "first_name",
        "last_name",
    )
    inlines = [
        OrderPassengerInline,
    ]
