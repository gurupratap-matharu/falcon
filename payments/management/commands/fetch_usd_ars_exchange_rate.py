from decimal import Decimal

from django.core.management.base import BaseCommand

import requests

from base.models import Settings


class Command(BaseCommand):
    """
    Fetch latest USD -> ARS exchange rate and store it in DB
    """

    help = "Fetch latest USD to ARS exchange rate"

    def handle(self, *args, **kwargs):
        self.stdout.write("getting latest exchange rate...")

        url = "https://v6.exchangerate-api.com/v6/10c3c21bb5def58b51bd3a31/latest/USD"

        response = requests.get(url)
        response.raise_for_status()

        rate = response.json().get("conversion_rates").get("ARS")

        self.stdout.write("1 USD = %s ARS" % rate)

        obj = Settings.objects.get(name="usd-ars")
        obj.dec_val = Decimal(rate)
        obj.save()

        self.stdout.write("All Done...")
