from typing import Any, Dict

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.shortcuts import get_object_or_404

from companies.models import Company


class OwnerMixin(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin):
    """
    Handy Mixin to allow company owners to do CRUD on only their own objects.
    """

    company = None
    permission_required = "trips.view_trip"

    def test_func(self):
        self.company = self.get_company()
        user = self.request.user
        return user.is_superuser or self.company.owner == user

    def get_company(self):
        return get_object_or_404(
            Company.objects.select_related("owner"), slug=self.kwargs["slug"]
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["company"] = self.company or self.get_company()
        return context
