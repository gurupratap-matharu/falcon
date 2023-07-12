from django.contrib import admin
from django.utils.html import format_html

from .models import Company, SeatChart


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "logo", "website", "email", "phone", "address", "owner")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "email")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("owner",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("owner")

    def logo(self, obj):
        if obj.cover:
            return format_html(
                '<img src="%s" alt="%s" width=50px height=50px />'
                % (obj.cover.url, obj.name)
            )
        return "-"

    logo.short_description = "Logo"


@admin.register(SeatChart)
class SeatChartAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "created_on", "updated_on")
    raw_id_fields = ("company",)
