from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _


class Settings(models.Model):
    """
    One time project level settings that we can edit from the admin interface
    """

    name = models.CharField(max_length=20, primary_key=True)
    char_val = models.CharField(max_length=100, blank=True, null=True, default=None)
    int_val = models.IntegerField(blank=True, null=True, default=None)
    bool_val = models.BooleanField(blank=True, null=True, default=None)
    dec_val = models.DecimalField(
        max_digits=11, decimal_places=2, blank=True, null=True, default=None
    )
    date_time_val = models.DateTimeField(blank=True, null=True, default=None)
    json_val = models.JSONField(
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("settings")
        verbose_name_plural = _("settings")

    def __str__(self):
        return f"{self.name}"
