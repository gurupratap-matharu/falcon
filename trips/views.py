import datetime
import logging
from typing import Any
from zoneinfo import ZoneInfo

from django.db.models import QuerySet
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, View

from .models import Trip

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
        if request.GET:
            logger.info("Veer url params: %s " % request.GET)
            request.session["q"] = request.GET

            # clear earlier trips session
            logger.info("clearing trips in session...")
            request.session.pop("trips", None)
        # TODO: Do API calls to get search results

        return redirect("trips:trip-list")


class TripListView(ListView):
    model = Trip
    template_name = "trips/trip_list.html"
    context_object_name: str = "trips"

    def get_queryset(self) -> QuerySet[Any]:

        if self.request.GET:
            logger.info("Veer url params: %s " % self.request.GET)
            self.request.session["q"] = self.request.GET

        qs = Trip.objects.exclude(
            departure__lt=datetime.datetime.now(tz=ZoneInfo("UTC"))
        )

        # Veer for now just return all trips that are today or the future
        # don't bother too much we'll filter later. let's get going
        return qs


class TripDetailView(DetailView):
    model = Trip
    context_object_name = "trip"
    template_name = "trips/trip_detail.html"
