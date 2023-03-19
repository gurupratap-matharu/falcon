import logging
import pdb
from typing import Any, Dict

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
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
class OwnerMixin(LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin):
    """
    Handy Mixin to allow company owners to do CRUD on only their own objects.
    """

    permission_required = "trips.view_trip"
    company = None

    def test_func(self):
        self.company = Company.objects.select_related("owner").get(
            slug=self.kwargs["slug"]
        )
        user = self.request.user
        return user.is_superuser or self.company.owner == user


class CompanyDashboardView(OwnerMixin, TemplateView):
    """
    Allow company staff to have single snapshot of all their trips
    """

    template_name = "companies/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["company"] = self.company  # <- Set in OwnerMixin
        return context
