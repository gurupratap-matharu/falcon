import logging

from django.views.generic import DetailView, ListView, TemplateView

from .mixins import OwnerMixin
from .models import Company

logger = logging.getLogger(__name__)

# Public Views


class CompanyListView(ListView):
    model = Company
    context_object_name = "companies"


class CompanyDetailView(DetailView):
    model = Company
    context_object_name = "company"


# Company Facing Views


class CompanyDashboardView(OwnerMixin, TemplateView):
    """
    Allow company staff to have single snapshot of all their trips
    """

    template_name = "companies/dashboard.html"
