from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Coupon(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text=_("Please use upper case with discount value eg: SUMMER10"),
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    discount = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentage value (0 to 100%)"),
    )
    active = models.BooleanField(default=True)

    def clean(self):

        # Don't allow valid_from date to be in the past
        if self.valid_from < timezone.now():
            raise ValidationError(
                {
                    "valid_from": _(
                        "Valid from date: %(valid_from)s cannot be in the past."
                    )
                },
                code="invalid",
                params={"valid_from": self.valid_from},
            )

        # Don't allow valid_to date to be less than valid_from date
        if self.valid_to < self.valid_from:
            raise ValidationError(
                {
                    "valid_to": _(
                        "Valid to: %(valid_to)s cannot be less than valid_from date: %(valid_from)s"
                    )
                },
                code="invalid",
                params={"valid_to": self.valid_to, "valid_from": self.valid_from},
            )

    def __str__(self):
        return self.code
