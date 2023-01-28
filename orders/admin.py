from django.contrib import admin

from .models import Order, OrderItem, Passenger


class PassengerInline(admin.TabularInline):
    model = Passenger
    exclude = (
        "document_type",
        "document_number",
        "birth_date",
        "gender",
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ("trip",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "trip", "price", "quantity")
    raw_id_fields = ("order", "trip")
    inlines = [PassengerInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "residence", "paid", "created_on")
    list_filter = ("paid", "created_on", "updated_on")
    readonly_fields = ("name", "email", "residence", "paid")
    inlines = [OrderItemInline]
