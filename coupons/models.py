import logging

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from coupons.managers import ValidManager

logger = logging.getLogger(__name__)


class Coupon(models.Model):
    """One time use coupons to apply a discount to a cart"""

    code = models.CharField(
        verbose_name=_("code"),
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
    valid_from = models.DateTimeField(_("valid from"), default=timezone.now)
    valid_to = models.DateTimeField(_("valid to"))
    discount = models.PositiveIntegerField(
        _("discount"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentage value (0 to 100%)"),
    )
    active = models.BooleanField(_("active"), default=True)

    class Meta:
        ordering = ("valid_to",)
        verbose_name = _("coupon")
        verbose_name_plural = _("coupons")

    objects = models.Manager()
    valid = ValidManager()

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

    def is_valid(self):
        """
        Determine if the coupon itself is valid or not.
        The criteria is:
            - coupon should not already be redeemed (i.e. be active)
            - valid_from < now < valid_to
        """

        now = timezone.now()
        return self.active and (self.valid_from < now < self.valid_to)

    def redeem(self):
        """Used when a coupon is redeemed by a user so that it cannot be used again"""

        if not self.is_valid():
            raise ValidationError("coupon is already invalid 🤷‍♀️")

        logger.info("deactivating coupon(💣):%s..." % self)

        self.active = False
        self.save(update_fields=["active"])

    def __str__(self):
        return f"{self.code}"
