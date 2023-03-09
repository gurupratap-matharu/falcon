import datetime
import logging
import pdb
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from companies.models import Company

from .forms import TripCreateForm
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
        qs = super().get_queryset()

        q = self.request.GET
        if q:
            # We got query params so let's filter the trips queryset
            logger.info("Veer url params: %s " % q)
            self.request.session["q"] = q

            origin = get_object_or_404(Location, name=q.get("origin"))
            destination = get_object_or_404(Location, name=q.get("destination"))
            departure_date = self.build_date(q.get("departure"))

            logger.info(
                "TripList(💋): origin: %s destination: %s departure: %s"
                % (origin, destination, departure_date)
            )

            # qs = qs.filter(
            #     origin=origin, destination=destination, departure__date=departure_date
            # )

        # other wise just return all the trips for now
        return qs

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["terminals"] = TERMINALS
        return context


class TripDetailView(DetailView):
    model = Trip
    context_object_name = "trip"
    template_name = "trips/trip_detail.html"


# Trip CRUD Private Views for company staff
class CRUDMixins(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin):
    pass


class CompanyTripListView(CRUDMixins, ListView):
    """Allow company staff to list their upcoming trips"""

    model = Trip
    template_name = "trips/company_trip_list.html"
    permission_required = "trips.view_trip"
    context_object_name = "trips"
    company = None

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["company"] = get_object_or_404(Company, slug=self.kwargs["slug"])

        return context

    def get_queryset(self) -> QuerySet[Any]:
        return Trip.active.for_company(company_slug=self.kwargs["slug"])


class TripCreateView(CRUDMixins, CreateView):
    """Allow company staff to create a new trip"""

    form_class = TripCreateForm
    template_name = "trips/trip_form.html"
    permission_required = "trips.add_trip"
    success_message = "Trip created successfully 💫"

    def form_valid(self, form):
        logger.info("trip form is valid(🌟)...")
        form.instance.company = get_object_or_404(Company, slug=self.kwargs["slug"])
        return super().form_valid(form)


class TripUpdateView(CRUDMixins, UpdateView):
    """Allow company staff to update their own trips"""

    model = Trip
    pk_url_kwarg = "id"
    form_class = TripCreateForm
    template_name = "trips/trip_form.html"
    permission_required = "trips.change_trip"
    success_message = "Trip updated successfully ✨"
