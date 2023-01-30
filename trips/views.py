import datetime
import logging
import pdb
from typing import Any
from zoneinfo import ZoneInfo

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from .models import Location, Trip
from .terminals import TERMINALS

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

    def build_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%d-%m-%Y").date()

    def get_queryset(self) -> QuerySet[Any]:
        q = self.request.GET
        if q:
            logger.info("Veer url params: %s " % q)
            self.request.session["q"] = q

        origin = get_object_or_404(Location, name=q.get("origin"))
        destination = get_object_or_404(Location, name=q.get("destination"))
        departure_date = self.build_date(q.get("departure"))

        logger.info(
            "TripList(💋): origin: %s destination: %s departure: %s"
            % (origin, destination, departure_date)
        )

        qs = Trip.active.filter(
            origin=origin, destination=destination, departure__date=departure_date
        )

        return qs

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["terminals"] = TERMINALS
        return context


class TripDetailView(DetailView):
    model = Trip
    context_object_name = "trip"
    template_name = "trips/trip_detail.html"
