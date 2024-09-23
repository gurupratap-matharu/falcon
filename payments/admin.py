from django.contrib import admin

from .models import ModoToken, WebhookMessage


@admin.register(WebhookMessage)
class WebhookMessage(admin.ModelAdmin):
    list_display = ("received_at", "provider")


@admin.register(ModoToken)
class ModoTokenAdmin(admin.ModelAdmin):
    pass
