import logging
from typing import Any, Dict

from django.views.generic import DetailView, ListView, TemplateView

from orders.models import Order, Passenger
from trips.models import Trip

from .mixins import OwnerMixin
from .models import Company, SeatChart

logger = logging.getLogger(__name__)

# Public Views


class CompanyListView(ListView):
    model = Company
    context_object_name = "companies"


class CompanyDetailView(DetailView):
    model = Company
    context_object_name = "company"


class CompanyLandingView(TemplateView):
    template_name = "companies/company_landing.html"


class CompanyBookView(DetailView):
    model = Company
    context_object_name = "company"
    template_name = "companies/company_book.html"


class CompanyHelpView(TemplateView):
    template_name = "companies/company_help.html"


# Company Facing Views


class CompanyDashboardView(OwnerMixin, TemplateView):
    """
    Allow company staff to have single snapshot of all their trips
    """

    template_name = "companies/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        slug = self.kwargs["slug"]

        context = super().get_context_data(**kwargs)
        context["trips"] = Trip.future.for_company(company_slug=slug, active=False)
        # context["kpis"] = Trip.past.kpis(company_slug=slug)
        context["kpis"] = {
            "occupancy": 74,
            "bookings": 234,
            "sales": 152443,
            "trips": 23,
        }

        return context


class SeatChartListView(OwnerMixin, TemplateView):
    template_name = "companies/seatchart_list.html"


class SeatChartDetailView(OwnerMixin, DetailView):
    model = SeatChart
    pk_url_kwarg = "id"
    context_object_name = "seatchart"


class AgencyListView(OwnerMixin, TemplateView):
    template_name = "companies/company_agency_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agencies"] = [
            {"name": "Las Toninas", "address": "Cordoba", "revenue": "1.67 M"},
            {"name": "Santa Clara", "address": "Santa Marta", "revenue": "1.63 M"},
            {"name": "Santa Teresita", "address": "Bahia Blanca", "revenue": "1.62 M"},
            {"name": "Mar Del Tuyu", "address": "Mar del plata", "revenue": "1.60 M"},
            {"name": "Quitilipi", "address": "Villa La Angostura", "revenue": "1.55 M"},
            {"name": "Las Mercedes", "address": "San Rafael", "revenue": "1.51 M"},
            {"name": "Machagai", "address": "Junin de los Andes", "revenue": "1.32 M"},
            {"name": "Agencia Saenz Pena", "address": "Chascomus", "revenue": "1.22 M"},
            {"name": "Resistencia", "address": "Resistencia", "revenue": "1.22 M"},
            {"name": "Viajes Pinamar", "address": "Pinamar", "revenue": "1.01 M"},
            {"name": "Ecopack Mendo Cargas", "address": "Mendoza", "revenue": "0.99 M"},
            {"name": "Junin", "address": "Junin De Los Andes", "revenue": "0.75 M"},
            {"name": "Agencia Mg Tandil", "address": "Tandil", "revenue": "0.75 M"},
        ]
        return context


class AgencyDetailView(OwnerMixin, TemplateView):
    template_name = "companies/company_agency_detail.html"


class LiveStatusView(OwnerMixin, TemplateView):
    template_name = "companies/live_status.html"


class PassengerListView(OwnerMixin, ListView):
    template_name = "companies/passengers.html"
    model = Passenger
    context_object_name = "passengers"
    paginate_by = 20


class OrderListView(OwnerMixin, ListView):
    template_name = "companies/company_order_list.html"
    model = Order
    context_object_name = "orders"
    paginate_by = 20


class WidgetView(DetailView):
    model = Company
    template_name = "companies/widget.js"
    context_object_name = "company"
    content_type = "text/javascript"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["num_routes"] = self.object.routes.count()

        return context
