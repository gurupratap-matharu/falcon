from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.text import gettext_lazy as _


class WebhookMessage(models.Model):
    """
    Generic table to store webhook json response in the DB
    """

    MERCADOPAGO = "MP"
    STRIPE = "SP"
    PROVIDER_CHOICES = [(MERCADOPAGO, "Mercado Pago"), (STRIPE, "Stripe")]

    provider = models.CharField(
        _("provider"), max_length=2, choices=PROVIDER_CHOICES, default=MERCADOPAGO
    )
    received_at = models.DateTimeField(help_text=_("When we received the message"))
    payload = models.JSONField(_("payload"), default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = _("webhook message")
        verbose_name_plural = _("webhook messages")
        indexes = [
            models.Index(fields=["received_at"]),
        ]

    def __str__(self):
        return f"{self.get_provider_display()}:{self.received_at}"


class ModoToken(models.Model):
    """
    Kind of singleton model to store a one time authentication token in the DB
    """

    token = models.CharField(_("token"), max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("modo token")
        verbose_name_plural = _("modo tokens")

    def __str__(self):
        return f"{self.updated_at}"
