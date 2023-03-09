import logging
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["company"] = get_object_or_404(Company, slug=self.kwargs["slug"])

        return context
