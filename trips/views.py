import logging
from datetime import datetime
from typing import Any, Dict

from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from django_weasyprint import WeasyTemplateResponseMixin

from companies.mixins import OwnerMixin
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
        return datetime.strptime(date_str, "%d-%m-%Y").date()

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
    pk_url_kwarg = "id"


# Trip CRUD Private Views for company staff
class CRUDMixins(OwnerMixin, SuccessMessageMixin):
    """
    Veer this is a handy mixin so that only company staff can do
    CRUD on their own objects.

    We simply inherit it from the (company) owner mixin and use it
    the views below.
    """

    def get_queryset(self) -> QuerySet[Any]:
        return Trip.future.for_company(company_slug=self.kwargs["slug"])


class CompanyTripListView(CRUDMixins, ListView):
    """Allow company staff to list their upcoming trips"""

    model = Trip
    template_name = "trips/company_trip_list.html"
    context_object_name = "trips"


class CompanyTripDetailView(CRUDMixins, DetailView):
    """
    Allow company staff to see passenger list for a trip
    This would be needed when the trip is about to depart.
    """

    model = Trip
    pk_url_kwarg = "id"
    context_object_name = "trip"
    template_name = "trips/company_trip_detail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # self.object refers to the trip of this view
        # add seats with related passengers to context
        context["seats"] = self.object.seats.select_related("passenger")

        return context


class TripCreateView(CRUDMixins, CreateView):
    """Allow company staff to create a new trip"""

    form_class = TripCreateForm
    template_name = "trips/trip_form.html"
    permission_required = "trips.add_trip"
    success_message = "Trip created successfully 💫"

    def form_valid(self, form):
        logger.info("trip form is valid(🌟)...")

        form.instance.company = self.company  # type:ignore
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.company.get_trip_list_url()  # type:ignore


class TripUpdateView(CRUDMixins, UpdateView):
    """Allow company staff to update their own trips"""

    model = Trip
    pk_url_kwarg = "id"
    context_object_name = "trip"
    form_class = TripCreateForm
    template_name = "trips/trip_form.html"
    permission_required = "trips.change_trip"
    success_message = "Trip updated successfully ✨"

    def get_success_url(self) -> str:
        return self.object.get_passenger_list_url()  # type:ignore


class TripPassengerPdfView(WeasyTemplateResponseMixin, CompanyTripDetailView):
    """
    Allows company staff to download the passenger list for a departing trip.

    Note:
        We inherit this view from CompanyTripDetailView
        So its already aware about the trip and company in its context.
        We simply overwrite the template name and pdf filename
    """

    template_name = "trips/trip_passengers_pdf.html"
    pdf_filename = "passengers.pdf"
