import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from .forms import CouponApplyForm
from .models import Coupon

logger = logging.getLogger(__name__)


class CouponApplyView(FormView):

    http_method_names = ["post"]
    success_url: str = reverse_lazy("cart:cart_detail")


@require_POST
def coupon_apply(request):
    """
    A simple view that validates a coupon
    """

    success_msg = "Coupon applied successfully! 📮"
    failure_msg = "Coupon is invalid 🤕"

    now = timezone.now()
    form = CouponApplyForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data["code"]

        logger.info("trying to apply coupon(📮):%s..." % code)

        try:
            coupon = Coupon.objects.get(
                code__iexact=code, valid_from__lte=now, valid_to__gte=now, active=True
            )

            request.session["coupon_id"] = coupon.id  # type:ignore
            messages.success(request, success_msg)
            logger.info("applied coupon(💸):%s..." % coupon)

            coupon.deactivate()

        except Coupon.DoesNotExist:
            logger.info("couldn't find coupon(📮):%s..." % code)
            messages.info(request, failure_msg)
            request.session["coupon_id"] = None

    return redirect("cart:cart_detail")
