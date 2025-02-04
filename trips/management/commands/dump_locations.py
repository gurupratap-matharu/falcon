import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Value

from trips.models import Location

logger = logging.getLogger(__name__)

IMP_LOCATIONS = ["BUE", "DELE", "ROS", "MDP", "CBA", "MZA", "IGU", "SFE", "POS"]


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

        imp_locs = Location.objects.filter(abbr__in=IMP_LOCATIONS).annotate(
            custom_order=Value(1)
        )

        other_locs = Location.objects.exclude(abbr__in=IMP_LOCATIONS).annotate(
            custom_order=Value(2)
        )

        all_locs = imp_locs.union(other_locs).order_by("custom_order")

        data = [
            {
                "label": f"({x.abbr}) {x.name} ({x.state}) ({x.country.name})",
                "value": x.abbr,
            }
            for x in all_locs
        ]

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        self.stdout.write("Important locations:%s" % IMP_LOCATIONS)
        self.stdout.write("Total locations:%s" % len(data))
        self.stdout.write("saved to:%s" % filepath)
        self.stdout.write("All Done 🚀💄✨")
