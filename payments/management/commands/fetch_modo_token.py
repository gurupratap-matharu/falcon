import logging

from django.core.management.base import BaseCommand

from payments.models import ModoToken
from payments.modo import fetch_token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Fetch modo authentication token via api and store it in the DB
    """

    help = "Fetch MODO authentication token via an API call and stores it in the DB"

    def handle(self, *args, **kwargs):
        token = fetch_token()

        logger.info("saving token to db...")

        if ModoToken.objects.exists():
            obj = ModoToken.objects.first()
            obj.token = token
            obj.save()
        else:
            obj = ModoToken.objects.create(token=token)

        logger.info("All Done 💄✨🚀")
