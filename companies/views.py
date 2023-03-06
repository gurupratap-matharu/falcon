import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from trips.models import Trip

from .models import Company

logger = logging.getLogger(__name__)

# Public Views


class CompanyListView(ListView):
    model = Company
    context_object_name = "companies"


class CompanyDetailView(DetailView):
    model = Company
    context_object_name = "company"


# Mixins
class OwnerMixin:
    """Filter any queryset for the logged in user"""

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_superuser:
            return qs[:5]

        return qs.filter(company__owner=self.request.user)


class OwnerEditMixin:
    """Attach current user to the owner attribute of the model"""

    def form_valid(self, form):

        logger.info("OwnerEditMixin: form is valid(🎩)")

        form.instance.owner = self.request.user  # 👈 Probably won't work
        return super().form_valid(form)


class OwnerTripMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    """Customize OwnerMixin for the Trip Model"""

    model = Trip
    context_object_name = "trips"
    fields = ("name", "departure", "arrival")  # 👈 Update this
    success_url = reverse_lazy("companies:manage_trip_list")


class OwnerTripEditMixin(OwnerTripMixin, OwnerEditMixin):
    template_name = "companies/manage_trip_form.html"


# Company Facing Views


class CompanyDashboardView(OwnerTripMixin, TemplateView):
    """
    Allow company staff to have single snapshot of all their trips
    """

    template_name = "companies/dashboard.html"
    permission_required = "trips.view_trip"


class ManageTripListView(OwnerTripMixin, ListView):
    """Allow company staff to list their upcoming trips"""

    template_name = "companies/manage_trip_list.html"
    permission_required = "trips.view_trip"


class TripCreateView(OwnerTripEditMixin, CreateView):
    """Allow company staff to create a new trip"""

    permission_required = "trips.add_trip"


class TripUpdateView(OwnerTripEditMixin, UpdateView):
    """Allow company staff to update their existing trip"""

    permission_required = "trips.change_trip"


class TripDeleteView(OwnerTripMixin, DeleteView):
    """Allow company staff to delete their existing trip"""

    template_name = "companies/manage_trip_delete.html"
    permission_required = "trips.delete_trip"
