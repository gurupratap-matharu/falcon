import logging

from django.views.generic import ListView

from .models import Company

logger = logging.getLogger(__name__)


class CompanyListView(ListView):
    model = Company
