from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)

from companies.models import Company


class OwnerMixin(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin):
    """
    Handy Mixin to allow company owners to do CRUD on only their own objects.
    """

    company = None
    permission_required = "trips.view_trip"

    def test_func(self):
        self.company = Company.objects.select_related("owner").get(
            slug=self.kwargs["slug"]
        )
        user = self.request.user
        return user.is_superuser or self.company.owner == user
