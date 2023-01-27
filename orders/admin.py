from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["trip"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "residence", "paid", "created_on")
    list_filter = ("paid", "created", "updated")
    inlines = [OrderItemInline]
