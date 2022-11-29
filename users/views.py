import logging

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView

from .forms import AccountDeleteForm, CustomUserCreationForm

logger = logging.getLogger(__name__)


class SignupPageView(CreateView):
    form_class = CustomUserCreationForm

    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class ProfilePageView(LoginRequiredMixin, TemplateView):
    template_name: str = "users/profile.html"


class AccountDeleteView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name: str = "users/account_delete.html"
    form_class = AccountDeleteForm
    success_url = reverse_lazy("pages:home")
    success_message: str = "Account deleted successfully!"

    def form_valid(self, form) -> HttpResponse:
        logger.info("deleting user: %s " % self.request.user)
        user = self.request.user
        logout(self.request)
        user.delete()

        return super().form_valid(form)
