import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from django_weasyprint import WeasyTemplateResponseMixin

from companies.mixins import OwnerMixin
from companies.models import SeatChart

from .forms import PriceGridForm, RecurrenceForm, TripCreateForm, TripSearchForm
from .models import Location, Route, Trip

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
            logger.info("search query (🔎):%s..." % request.GET)
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
    invalid_query_msg = " Please try again 🙏"
    form_class = TripSearchForm

    def get_date_ladder(self):
        departure = self.request.GET.get("departure")
        date = datetime.strptime(departure, "%d-%m-%Y")
        ladder = (date + timedelta(days=x) for x in range(-1, 2))

        return [x for x in ladder if x >= datetime.now()]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["date_ladder"] = self.get_date_ladder()
        return context

    def get(self, request, *args, **kwargs):
        """
        Overwrite this method of validate if the search query params are valid
        else redirect to home with a valid message.
        """

        q = request.GET

        try:
            form = self.form_class(q)
            form.validate()

        except Exception as e:
            messages.info(request, str(e) + self.invalid_query_msg)
            return redirect(reverse_lazy("pages:home"))

        logger.info("search query:%s..." % q)
        request.session["q"] = q

        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        q = self.request.GET
        qs = Trip.future.search(
            origin=q.get("origin"),
            destination=q.get("destination"),
            departure=q.get("departure"),
            company_slug=q.get("company"),
            ordering=q.get("ordering"),
        )

        return qs


class TripDetailView(DetailView):
    model = Trip
    context_object_name = "trip"
    template_name = "trips/trip_detail.html"
    pk_url_kwarg = "id"

    def get_object(self):
        trip = get_object_or_404(
            Trip.objects.select_related("company", "route", "origin", "destination"),
            id=self.kwargs["id"],
        )
        return trip


# Trip CRUD Private Views for company staff
class CRUDMixins(OwnerMixin, SuccessMessageMixin):
    """
    Veer this is a handy mixin so that only company staff can do
    CRUD on their own objects.

    We simply inherit it from the (company) owner mixin and use it
    the views below.
    """

    pass


class CompanyRouteListView(CRUDMixins, ListView):
    """Shows all the routes for a company"""

    model = Route
    template_name = "trips/company_route_list.html"
    context_object_name = "routes"

    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs.filter(company__slug=self.kwargs["slug"])
            .select_related("company", "origin", "destination")
            .order_by("name")
        )


class CompanyRouteDetailView(CRUDMixins, DetailView):
    """Show details on one particular route for a company"""

    model = Route
    pk_url_kwarg = "id"
    context_object_name = "route"
    template_name = "trips/company_route_detail.html"

    def get_object(self):
        route = get_object_or_404(
            Route.objects.select_related("company", "origin", "destination"),
            id=self.kwargs["id"],
        )
        return route

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["stops"] = self.object.stops.select_related("name")
        return context


@method_decorator(staff_member_required, name="dispatch")
class AdminRouteDetailView(DetailView):
    """Custom admin view to show all trips for a route"""

    model = Route
    pk_url_kwarg = "route_id"
    context_object_name = "route"
    template_name = "trips/admin_route_detail.html"


class CompanyTripListView(CRUDMixins, ListView):
    """Allow company staff to list their upcoming trips"""

    model = Trip
    template_name = "trips/company_trip_list.html"
    context_object_name = "trips"

    def get_queryset(self) -> QuerySet[Any]:
        return Trip.future.for_company(company_slug=self.kwargs["slug"], active=False)


class CompanyTripDetailView(CRUDMixins, DetailView):
    """
    Allow company staff to see passenger list for a trip
    This would be needed when the trip is about to depart.
    """

    model = Trip
    pk_url_kwarg = "id"
    context_object_name = "trip"
    template_name = "trips/company_trip_detail.html"

    def get_queryset(self) -> QuerySet[Any]:
        return Trip.future.for_company(company_slug=self.kwargs["slug"], active=False)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # self.object refers to the trip of this view
        # add seats with related passengers to context
        context["seats"] = self.object.seats.order_by("seat_number").select_related(
            "passenger"
        )

        return context


class TripCreateView(CRUDMixins, CreateView):
    """Allow company staff to create a new trip"""

    form_class = TripCreateForm
    template_name = "trips/trip_form.html"
    permission_required = "trips.add_trip"
    success_message = "Trip created successfully 💫"

    def form_valid(self, form):
        logger.info("trip form is valid(🌟)...")

        form.instance.company = self.company

        # Save trip and get http response
        response = super().form_valid(form)

        # Create the seats
        self.create_trip_seats(trip=form.instance)

        return response

    def get_success_url(self) -> str:
        return self.company.get_trip_list_url()  # type:ignore

    def create_trip_seats(self, trip):
        """
        After the trip object is created we call this handy method
        to create relevant seats from the provided seatchart.
        """

        # Pull the seatchart from DB
        title = self.request.POST.get("seatchart")
        seatchart = get_object_or_404(SeatChart, title=title, company=self.company)

        # Find which seat numbers need to be created for both floors
        lower = seatchart.json.get("lower", {}).get("enabledSeats", [])
        upper = seatchart.json.get("upper", {}).get("enabledSeats", [])

        logger.info("lower seats: %s" % lower)
        logger.info("upper seats: %s" % upper)

        seat_numbers = lower + upper

        if not seat_numbers:
            messages.warning(self.request, "SeatChart is invalid!")

        # Finally create the seats
        seats = trip.create_seats(*seat_numbers)
        logger.info("created seats: %s" % seats)

        return seats


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


class LocationListView(ListView):
    model = Location
    context_object_name = "locations"
    template_name = "trips/location_list.html"


class LocationDetailView(DetailView):
    model = Location
    context_object_name = "location"
    template_name = "trips/location_detail.html"


class RecurrenceView(CRUDMixins, FormView):
    form_class = RecurrenceForm
    template_name = "trips/recurrence_form.html"
    permission_required = "trips.change_trip"
    success_message = "Recurring trips created successfully!"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["trip"] = get_object_or_404(Trip, id=self.kwargs["id"])
        return context

    def form_valid(self, form):
        trip = get_object_or_404(Trip, id=self.kwargs["id"])

        logger.info("RecurrenceForm is valid...")
        logger.info("Trip:%s..." % trip)

        trips = form.save(trip=trip)

        messages.success(self.request, f"Total Occurrences: {len(trips)}")

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.company.get_trip_list_url()


@method_decorator(staff_member_required, name="dispatch")
class PriceGridView(SuccessMessageMixin, FormView):
    form_class = PriceGridForm
    template_name = "trips/price_grid.html"
    success_message = "Price grid updated successfully 💰"

    def get_route(self):
        self.route = get_object_or_404(Route, id=self.kwargs["route_id"])
        return self.route

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["route"] = self.get_route()
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class=self.form_class)

        route = self.get_route()
        qs = route.stops.select_related("name")

        form.fields["origin"].queryset = qs
        form.fields["destination"].queryset = qs

        return form

    def form_valid(self, form):
        form.save(route=self.route)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("trips:price-grid", kwargs={"route_id": str(self.route.id)})
