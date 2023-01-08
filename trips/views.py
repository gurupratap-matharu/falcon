import logging
from typing import Any, Dict

from django.shortcuts import redirect
from django.views.generic import TemplateView, View

from cart.cart import Cart

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
