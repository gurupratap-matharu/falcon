from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from orders.validators import validate_birth_date


class BirthDateValidatorTests(SimpleTestCase):
    """
    Test suite to verify if a birth date is valid or not.
    We consider any age between 1 - 99 years as valid. 😌
    """

    def test_person_more_than_hundred_years_old(self):
        birth_date = date.today() - timedelta(days=40000)

        with self.assertRaises(ValidationError):
            validate_birth_date(born=birth_date)

    def test_person_not_yet_born(self):
        birth_date = date.today() + timedelta(days=1)

        with self.assertRaises(ValidationError):
            validate_birth_date(born=birth_date)

    def test_person_born_today(self):
        # No exception should be raised so we don't assert anything and
        # the test passes. Person born today is valid for us!
        birth_date = date.today()
        validate_birth_date(born=birth_date)

    def test_normal_person_birth_day(self):
        birth_date = date.today() - timedelta(days=2000)
        validate_birth_date(born=birth_date)
