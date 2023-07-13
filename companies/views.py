import logging
from typing import Any, Dict

from django.views.generic import DetailView, ListView, TemplateView

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
        context["kpis"] = Trip.past.kpis(company_slug=slug)

        return context


class SeatChartListView(OwnerMixin, TemplateView):
    template_name = "companies/seatchart_list.html"


class SeatChartDetailView(OwnerMixin, DetailView):
    model = SeatChart
    pk_url_kwarg = "id"
    context_object_name = "seatchart"
