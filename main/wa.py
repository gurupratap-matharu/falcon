import json
import logging

from django.conf import settings

import requests

logger = logging.getLogger(__name__)

headers = {
    "Content-type": "application/json",
    "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
}

url = f"https://graph.facebook.com/v20.0/{settings.WA_PHONE_ID}/messages"


def send_wa_message(data):
    try:
        logger.info("sending whatsapp message...")
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        logger.error(err)

    except requests.exceptions.ConnectionError as err:
        logger.error("Connection Error!", err)

    except requests.exceptions.Timeout as err:
        logger.warn("Request Timed out", err)

    except requests.exceptions.RequestException as err:
        logger.critical("Catastrophic. Could not talk to whatsapp!", err)

    else:
        logger.info(response.text)
        return response


def get_document_payload(recipient="54111550254191", context=None):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "document",
        "document": {
            "link": context["link"],
            "caption": context["caption"],
            "filename": context["filename"],
        },
    }
    return json.dumps(data)
