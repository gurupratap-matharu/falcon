import csv
import datetime
import logging
from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html

from trips.admin import TripOrderInline

from .models import Order, OrderItem, Passenger

logger = logging.getLogger(__name__)

admin.site.empty_value_display = "(None)"


def export_to_csv(modeladmin, request, queryset):
    """
    Custom OrderAdmin action to export selected orders to a CSV file.
    TODO: Remove uuid field and add normal counter field, remove updated_on field
    """

    opts = modeladmin.model._meta
    content_disposition = f"attachment; filename={opts.verbose_name_plural}.csv"

    fields = [
        field
        for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
    ]

    header_row = [field.verbose_name for field in fields]

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = content_disposition

    writer = csv.writer(response)
    writer.writerow(header_row)

    for obj in queryset:
        data_row = []

        for field in fields:
            value = getattr(obj, field.name)

            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")

            data_row.append(value)

        writer.writerow(data_row)

    return response


export_to_csv.short_description = "Export to CSV"


class OrderPassengerInline(admin.TabularInline):
    model = Order.passengers.through
    readonly_fields = (
        "order",
        "passenger",
    )
    extra = 0
    classes = ("collapse",)
    can_delete = False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "trip", "quantity", "price", "seats")
    readonly_fields = ("order", "trip", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "residence",
        "paid",
        "order_payment",
        "invoice_pdf",
        "order_coupon",
        "created_on",
    )
    exclude = ("passengers",)
    list_filter = ("paid", "created_on", "updated_on")
    raw_id_fields = ("coupon",)
    inlines = [
        OrderPassengerInline,
        TripOrderInline,
    ]
    actions = [export_to_csv]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        qs = super().get_queryset(request)
        return qs.select_related("coupon")

    def order_payment(self, obj):
        url = obj.get_stripe_url()
        return format_html('<a href="{}" target="_blank">View</a>', url)

    def invoice_pdf(self, obj):
        url = reverse("orders:admin_invoice_pdf", kwargs={"order_id": str(obj.id)})
        return format_html('<a href="{}" target="_blank">PDF</a>', url)

    def order_coupon(self, obj):
        return bool(obj.coupon)

    invoice_pdf.short_description = "Invoice"
    order_coupon.short_description = "Coupon"
    order_coupon.boolean = True
    order_payment.short_description = "Transaction"


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = (
        "name",
        "document_type",
        "document_number",
        "nationality",
        "gender",
        "phone_number",
    )
    search_fields = ("first_name", "last_name")
    inlines = [
        OrderPassengerInline,
    ]

    def name(self, obj):
        return obj.get_full_name()
