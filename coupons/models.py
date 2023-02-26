from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Coupon(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text=_("Please use capital letters without spaces. Ex: SUMMER10"),
        validators=[
            RegexValidator(
                "^[A-Z0-9]*$",
                "Please use only uppercase letters and numbers without spaces.",
            )
        ],
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    discount = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentage value (0 to 100%)"),
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("valid_to",)

    def clean(self):

        # Don't allow valid_from date to be in the past
        if self.valid_from.date() < timezone.now().date():
            raise ValidationError(
                {"valid_from": _("Valid from date cannot be in the past.")},
                code="invalid",
            )

        # Don't allow valid_to date to be less than valid_from date
        if self.valid_to and (self.valid_to < self.valid_from):
            raise ValidationError(
                {"valid_to": _("Valid to date cannot be less than Valid from date")},
                code="invalid",
            )

    def __str__(self):
        return self.code
