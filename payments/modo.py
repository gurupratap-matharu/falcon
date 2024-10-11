import logging

from django.conf import settings

import requests

from payments.models import ModoToken

logger = logging.getLogger(__name__)


def create_payment_intent(order):
    """
    Call the MODO api and create a payment intent for a bus ticket.
    """

    token = ModoToken.objects.first().token

    headers = {
        "User-Agent": "Ventanita",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "productName": f"Bus tickets for {order.name}",
        "price": float(order.get_total_cost() / 1000),  # <-- reducing for modo
        "quantity": 1,
        "currency": "ARS",
        "storeId": settings.MODO_STORE_ID,
        "externalIntentionId": str(order.id),
        "message": "This secret message is taken till the webhook",
    }

    logger.info("headers:%s", headers)
    logger.info("data:%s", payload)

    try:
        logger.info("calling modo api...")

        url = settings.MODO_PAYMENT_INTENT_URL
        response = requests.post(url=url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        logger.error(err)

    except requests.exceptions.ConnectionError as err:
        logger.error("Connection error!", err)

    except requests.exceptions.Timeout as err:
        logger.warn("Request timed out", err)

    except requests.exceptions.RequestException as err:
        logger.critical("Catastrophic. Could not talk to MODO.", err)

    else:
        logger.info(response.text)
        return response


def fetch_token():
    url = settings.MODO_TOKEN_URL
    headers = {"User-Agent": "Ventanita", "Content-type": "application/json"}
    payload = {
        "username": settings.MODO_CLIENT_ID,
        "password": settings.MODO_CLIENT_SECRET,
    }

    try:
        logger.info("fetching modo token...")
        response = requests.post(url=url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        logger.error(err)

    except requests.exceptions.ConnectionError as err:
        logger.error("Connection error!", err)

    except requests.exceptions.Timeout as err:
        logger.warn("Request timed out", err)

    except requests.exceptions.RequestException as err:
        logger.critical("Catastrophic. Could not talk to MODO.", err)

    else:
        logger.info("token received...")
        logger.info(response.text)
        return response.json()["accessToken"]
