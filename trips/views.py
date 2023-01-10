import json
import logging
from typing import Any, Dict

from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import TemplateView, View

logger = logging.getLogger(__name__)


class TripSearchView(View):
    """
    The main search engine of our app to search for trips either in our database
    or via an API.

    This view holds the responsibility of getting the trip information from a user
    and generative a list of trips which is passed as context to the trip list view.
    """

    def get(self, request):
        # Add search query to session
        request.session["q"] = request.GET
        logger.info("Veer url params: %s " % request.GET)
        # TODO: Do API calls to get search results

        return redirect("trips:trip-list")


class TripListView(TemplateView):
    template_name = "trips/trip_list.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        with open(settings.TRIPS_PATH) as f:
            context["trips"] = json.load(f)

        return context
