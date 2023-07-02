import logging

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class ValidManager(models.Manager):
    """
    Coupon model manager that allows to query only valid coupons.
    """

    def get_queryset(self):
        """
        Filter out only valid coupons
        """

        logger.info("showing only active couponts (🎟️)...")

        now = timezone.now()
        qs = super().get_queryset()
        qs = qs.filter(valid_from__lte=now, valid_to__gte=now, active=True)

        return qs
