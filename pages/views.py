from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.http import FileResponse, HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django.views.generic import FormView, TemplateView

from .forms import ContactForm, FeedbackForm


class HomePageView(TemplateView):
    template_name: str = "pages/dashboard.html"


class AboutPageView(TemplateView):
    template_name: str = "pages/about.html"


class TermsPageView(TemplateView):
    template_name: str = "pages/terms.html"


class PrivacyPageView(TemplateView):
    template_name: str = "pages/privacy.html"


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


class BaseFullScreenPageView(TemplateView):
    template_name = "layouts/base-fullscreen.html"
