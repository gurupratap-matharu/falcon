import logging
import random
import uuid
from typing import Any

from django.db.models import QuerySet
from django.shortcuts import redirect
from django.views.generic import ListView, View

from .models import Trip

logger = logging.getLogger(__name__)


def generate_trip_data():
    """Helper method to generate fake trip data"""

    CITIES = ["BUE", "MZA", "CBA", "ROS", "MDP", "BAR", "MIS", "CAL", "USH"]

    return {
        "tripId": str(uuid.uuid4()),
        "company": random.choice(
            [
                "Andesmar",
                "Chevalier",
                "Via Bariloche",
                "Patagonia",
                "Pullman",
                "Cata",
                "Plusmar",
                "Andreani",
            ]
        ),
        "imageUrl": f"bus{random.randint(1, 7)}.jpg",
        "availableSeats": random.randint(1, 10),
        "seatType": random.choice(["Cama", "Semicama", "Executive"]),
        "departure": f"{random.randint(0, 23):02}:{random.randint(0, 60):02}",
        "arrival": f"{random.randint(0, 23):02}:{random.randint(0, 60):02}",
        "duration": random.randint(1, 24),
        "origin": random.choice(CITIES),
        "destination": random.choice(CITIES),
        "mode": random.choice(["Direct", "SemiDirect"]),
        "price": random.randint(1000, 10000),
    }


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

            # clear earlier trips session
            logger.info("clearing trips in session...")
            self.request.session.pop("trips", None)

        return super().get_queryset()

    # def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
    #     context = super().get_context_data(**kwargs)

    #     # Either get current trips from session or set default

    #     context["trips"] = self.request.session.setdefault(
    #         "trips", [generate_trip_data() for _ in range(10)]
    #     )

    #     order_by = self.request.GET.get("order")
    #     if order_by:
    #         reverse = order_by == "price"
    #         context["trips"] = sorted(
    #             context["trips"], key=lambda d: d["price"], reverse=reverse
    #         )

    #     return context
