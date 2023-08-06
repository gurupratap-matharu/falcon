import logging

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView

from .forms import AccountDeleteForm, CustomUserCreationForm, ProfileEditForm

logger = logging.getLogger(__name__)


class SignupPageView(CreateView):
    form_class = CustomUserCreationForm

    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class ProfilePageView(LoginRequiredMixin, TemplateView):
    template_name: str = "users/profile.html"


class AccountSettingsView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name: str = "users/settings.html"
    form_class = ProfileEditForm
    success_url = reverse_lazy("users:profile")
    success_message: str = "Profile updated successfully!"

    def form_valid(self, form) -> HttpResponse:
        logger.info("updating profile for: %s " % self.request.user)
        cd = form.cleaned_data
        user = self.request.user

        user.first_name = cd["first_name"]
        user.last_name = cd["last_name"]
        user.bio = cd["bio"]
        user.location = cd["location"]
        user.personal_website = cd["personal_website"]
        user.save()

        return super().form_valid(form)

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """

        user = self.request.user
        initial = super().get_initial()

        initial["first_name"] = user.first_name
        initial["last_name"] = user.last_name
        initial["bio"] = user.bio
        initial["location"] = user.location
        initial["personal_website"] = user.personal_website

        return initial


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
