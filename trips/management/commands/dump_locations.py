import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.functions import Length

from trips.models import Location

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Dump all locations into a json for using in autocomplete widget
    in the search form.
    """

    def handle(self, **options):
        JSON_DIR = settings.STATIC_ROOT / "assets" / "json"
        JSON_DIR.mkdir(parents=True, exist_ok=True)

        filename = "terminals.json"

        filepath = JSON_DIR / filename

        all_locations = [
            {
                "label": f"({x.abbr}) {x.name} ({x.state}) ({x.country.name})",
                "value": x.id,
            }
            for x in Location.objects.order_by(Length("abbr"))
        ]

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(all_locations, f, ensure_ascii=False)

        self.stdout.write("saved to:%s" % filepath)
        self.stdout.write("All Done 🚀💄✨")
