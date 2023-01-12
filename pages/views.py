import logging
from pprint import pformat
from typing import Any, Dict

import mercadopago
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http import FileResponse, HttpRequest, HttpResponse
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, FormView, TemplateView

from .forms import ContactForm, FeedbackForm

logger = logging.getLogger(__name__)


mercado_pago = mercadopago.SDK(settings.MP_ACCESS_TOKEN)


CustomUser = get_user_model()


class HomePageView(TemplateView):
    template_name: str = "pages/home.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        q = self.request.session.get("q")
        context["q"] = q or {}

        return context


class SeatsView(TemplateView):
    template_name: str = "pages/seats.html"


class OrderView(TemplateView):
    template_name: str = "pages/order.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        passenger = self.request.session.get("passenger")
        context["passenger"] = passenger or {}

        return context


class PaymentView(TemplateView):
    template_name: str = "pages/payment.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.request.session["passenger"] = self.request.GET
        logger.info("Veer storing passenger data in session: %s " % self.request.GET)

        current_site = get_current_site(self.request)

        back_url_success = "http://%s%s" % (
            current_site.domain,
            reverse_lazy("pages:payment-success"),
        )
        back_url_failure = "http://%s%s" % (
            current_site.domain,
            reverse_lazy("pages:payment-fail"),
        )

        picture_url = "http://%s%s" % (
            current_site.domain,
            static("assets/img/bus/bus4.jpg"),
        )

        logger.info("Veer back_url_success: %s", back_url_success)
        logger.info("Veer back_url_failure: %s", back_url_failure)
        logger.info("Veer picture_url: %s", picture_url)

        # Create mercado page preference
        preference_data = {
            "items": [
                {
                    "id": "Trip-id-1234",
                    "title": "My Bus ticket",
                    "currency_id": "ARS",
                    "quantity": 1,
                    "picture_url": picture_url,
                    "description": "BUE - MZA Cama Tommorow Night",
                    "category_id": "Andesmar",
                    "unit_price": 1.23,
                }
            ],
            "payer": {
                "name": "Juan",
                "surname": "Lopez",
                "email": "juan.lopez@email.com",
                "phone": {"area_code": "11", "number": "4444-4444"},
                "identification": {"type": "DNI", "number": "12345678"},
                "address": {
                    "street_name": "Street",
                    "street_number": 123,
                    "zip_code": "5700",
                },
            },
            "back_urls": {
                "success": back_url_success,
                "failure": back_url_failure,
                "pending": "",
            },
            "auto_return": "approved",
            "notification_url": "https://webhook.site/a40b5b6a-26a9-4261-9a2c-1b9b7fa9fb85",  # temporary webhook
            "statement_descriptor": "Falcon",
            "external_reference": "Reference_1234",
            "binary_mode": True,
        }

        preference_response = mercado_pago.preference().create(preference_data)

        context["preference"] = preference_response["response"]
        context["mp_public_key"] = settings.MP_PUBLIC_KEY
        return context


class PaymentSuccessView(TemplateView):
    template_name: str = "pages/payment_success.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        # Just printing what mercado pago sends back in case of successful payment
        logger.info("veer mercado pago says %s" % self.request.GET)

        return super().get_context_data(**kwargs)


class PaymentFailView(TemplateView):
    template_name: str = "pages/payment_fail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        # Just printing what mercado pago sends back in case of failed payment
        logger.info("veer mercado pago says %s" % self.request.GET)

        return super().get_context_data(**kwargs)


class DashboardPageView(TemplateView):
    template_name: str = "pages/dashboard.html"


class AboutPageView(TemplateView):
    template_name: str = "pages/about.html"


class TermsPageView(TemplateView):
    template_name: str = "pages/terms.html"


class PrivacyPageView(TemplateView):
    template_name: str = "pages/privacy.html"


class PublicProfilePageView(DetailView):
    """
    Renders a public profile view which is accessible at
    domain.com/<username-slug>/

    This view is meant to be accessible for anyone even anonymous users
    The endpoint serves as a handle for our site.

    We only show very basic info of a user in the corresponding template.
    """

    model = CustomUser
    context_object_name: str = "user"
    template_name: str = "pages/public_profile.html"
    slug_field: str = "username"


class ContactPageView(SuccessMessageMixin, FormView):
    template_name: str = "pages/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("pages:home")
    success_message: str = "Message sent successfully 🤞"

    def form_valid(self, form) -> HttpResponse:
        form.send_mail()  # type: ignore
        return super().form_valid(form)


class FeedbackPageView(SuccessMessageMixin, FormView):
    template_name: str = "pages/feedback.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("pages:home")
    success_message: str = "Thank you for your feedback 💓"

    def form_valid(self, form) -> HttpResponse:
        form.send_mail()  # type: ignore
        return super().form_valid(form)


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # one day
def favicon(request: HttpRequest) -> FileResponse:
    """
    You might wonder why you need a separate view, rather than relying on Django’s staticfiles app.
    The reason is that staticfiles only serves files from within the STATIC_URL prefix, like static/.

    Thus staticfiles can only serve /static/favicon.ico, whilst the favicon needs to be served at exactly /favicon.ico (without a <link>).

    Say if the project is accessed at an endpoint that returns a simple JSON and doesn't use the
    base.html file then the favicon won't show up.

    This endpoint acts as a fall back to supply the necessary icon at /favicon.ico
    """

    file = (settings.BASE_DIR / "static" / "assets" / "img" / "favicon.png").open("rb")
    return FileResponse(file, headers={"Content-Type": "image/x-icon"})


class BasePageView(TemplateView):
    template_name = "layouts/base.html"


class BaseHeroPageView(TemplateView):
    template_name = "layouts/base-hero.html"
