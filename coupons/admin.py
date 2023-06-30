from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount", "valid", "redeemed")
    list_filter = ("active", "valid_from", "valid_to")
    search_fields = ("code",)

    @admin.display(boolean=True, description="Is Valid?")
    def valid(self, obj):
        return obj.is_valid()

    @admin.display(boolean=True, description="Is Redeemed?")
    def redeemed(self, obj):
        return not obj.active
