import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)


class SignupPageView(CreateView):
    form_class = CustomUserCreationForm

    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class ProfilePageView(LoginRequiredMixin, TemplateView):
    template_name: str = "users/profile.html"
