from datetime import datetime, timedelta
from random import randint
from zoneinfo import ZoneInfo

import factory
from factory import fuzzy
from faker import Faker

from .models import Coupon

fake = Faker()


class CouponFactory(factory.django.DjangoModelFactory):
    """Factory to create random coupons for our site"""

    class Meta:
        model = Coupon
        django_get_or_create = ("code",)

    code = factory.LazyAttribute(lambda o: fake.word().upper() + str(o.discount))
    valid_from = fuzzy.FuzzyDateTime(
        start_dt=datetime.now(tz=ZoneInfo("UTC")) - timedelta(days=90),
        end_dt=datetime.now(tz=ZoneInfo("UTC")) + timedelta(days=90),
    )
    valid_to = factory.LazyAttribute(
        lambda o: o.valid_from + timedelta(days=randint(7, 365))  # nosec
    )
    discount = fuzzy.FuzzyInteger(low=1, high=100)
    active = fuzzy.FuzzyChoice(choices=(True, False))


class CouponValidFactory(CouponFactory):
    """Always create a valid coupon"""

    valid_from = datetime.now(tz=ZoneInfo("UTC"))
    valid_to = factory.LazyAttribute(lambda o: o.valid_from + timedelta(days=7))
    active = True


class CouponInvalidFactory(CouponFactory):
    """Always create an invalid coupon"""

    active = False
