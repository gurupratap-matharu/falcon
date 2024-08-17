from django.contrib import admin

from .models import WebhookMessage


@admin.register(WebhookMessage)
class WebhookMessage(admin.ModelAdmin):
    list_display = ("received_at", "provider")
