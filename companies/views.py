import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import DetailView, ListView, TemplateView

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


class CompanyDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Allow company staff to have single snapshot of all their trips
    """

    template_name = "companies/dashboard.html"
    permission_required = "trips.view_trip"


class ManageTripListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Allow company staff to list their upcoming trips"""

    template_name = "companies/manage_trip_list.html"
    permission_required = "trips.view_trip"
