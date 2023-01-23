from django.contrib import admin
from django.utils.html import format_html

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "logo", "website", "email", "phone", "address")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "email")
    prepopulated_fields = {"slug": ("name",)}

    def logo(self, obj):
        if obj.cover:
            return format_html(
                '<img src="%s" alt="%s" width=50px height=50px />'
                % (obj.cover.url, obj.name)
            )
        return "-"

    logo.short_description = "Logo"
