import logging

from django.views.generic import DetailView, ListView

from .models import Company

logger = logging.getLogger(__name__)


class CompanyListView(ListView):
    model = Company
    context_object_name = "companies"


class CompanyDetailView(DetailView):
    model = Company
    context_object_name = "company"
