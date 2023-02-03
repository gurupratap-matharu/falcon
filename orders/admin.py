from django.contrib import admin

from .models import Order, OrderItem, Passenger


class PassengerInline(admin.TabularInline):
    model = Passenger
    readonly_fields = (
        "first_name",
        "last_name",
        "nationality",
        "seat_number",
        "phone_number",
    )
    exclude = (
        "trip",
        "document_type",
        "document_number",
        "birth_date",
        "gender",
    )
    extra = 0
    can_delete = False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("trip", "quantity", "price")
    extra = 0
    can_delete = False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "trip", "price", "quantity")
    raw_id_fields = ("order", "trip")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "residence", "paid", "created_on")
    list_filter = ("paid", "created_on", "updated_on")
    readonly_fields = ("name", "email", "residence", "paid")
    inlines = [PassengerInline, OrderItemInline]
