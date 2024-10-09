from django.contrib import admin

from base.models import Settings


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    pass
