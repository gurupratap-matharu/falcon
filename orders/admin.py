import csv
import datetime
import logging

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe

from trips.admin import TripOrderInline

from .models import Order, OrderItem, Passenger

logger = logging.getLogger(__name__)


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
    can_delete = False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "trip", "quantity", "price", "seats")
    readonly_fields = ("order", "trip", "price", "seats", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "residence",
        "paid",
        "created_on",
        "order_payment",
        "order_pdf",
    )
    exclude = ("passengers",)
    list_filter = ("paid", "created_on", "updated_on")
    inlines = [
        OrderPassengerInline,
        TripOrderInline,
    ]
    actions = [export_to_csv]

    def order_payment(self, obj):
        url = obj.get_stripe_url()
        html = f'<a href="{url}" target="_blank">View</a>' if url else ""
        return mark_safe(html)  # nosec

    def order_pdf(self, obj):
        url = reverse("orders:admin_order_pdf", kwargs={"order_id": str(obj.id)})
        html = f'<a href="{url}" target="_blank" download="{obj.name}">PDF</a>'
        return mark_safe(html)  # nosec

    order_pdf.short_description = "Invoice"


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
