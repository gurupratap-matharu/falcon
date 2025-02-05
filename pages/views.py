import logging
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, FormView, TemplateView

from .forms import ContactForm, FeedbackForm

logger = logging.getLogger(__name__)


CustomUser = get_user_model()

COMMON_TIMEZONES = {
    "UTC": "Europe/London",
    "Paris": "Europe/Paris",
    "New York": "America/New_York",
}


class HomePageView(TemplateView):
    template_name: str = "pages/home.html"


class AboutPageView(TemplateView):
    template_name: str = "pages/about.html"


class TermsPageView(TemplateView):
    template_name: str = "pages/terms.html"


class PrivacyPageView(TemplateView):
    template_name: str = "pages/privacy.html"


class SitemapPageView(TemplateView):
    template_name: str = "pages/sitemap.html"


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


class RobotsTxtView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain"


class IndexNow(TemplateView):
    template_name = "3520839d70e34eb79e009ddb5fedef3b.txt"
    content_type = "text/plain"


@require_GET
@cache_control(max_age=60 * 60 * 24, immutable=True, public=True)  # one day
def favicon(request: HttpRequest) -> FileResponse:
    """
    You might wonder why you need a separate view, rather than relying on Django’s staticfiles app.
    The reason is that staticfiles only serves files from within the STATIC_URL prefix, like static/.

    Thus staticfiles can only serve /static/favicon.ico,
    whilst the favicon needs to be served at exactly /favicon.ico (without a <link>).

    Say if the project is accessed at an endpoint that returns a simple JSON and doesn't use the
    base.html file then the favicon won't show up.

    This endpoint acts as a fall back to supply the necessary icon at /favicon.ico
    """

    file = (
        settings.BASE_DIR
        / "static"
        / "assets"
        / "icons"
        / "favicons"
        / "apple-touch-icon.png"
    ).open("rb")
    return FileResponse(file, headers={"Content-Type": "image/x-icon"})


class LandingPageView(TemplateView):
    template_name = "pages/landing.html"


class HelpPageView(TemplateView):
    template_name = "pages/help.html"


class IndexPageView(TemplateView):
    template_name = "layouts/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["timezones"] = COMMON_TIMEZONES
        return context

    def post(self, request, *args, **kwargs):

        request.session["django_timezone"] = request.POST["timezone"]

        logger.info("request.POST:%s" % request.POST)
        logger.info("request.session:%s" % request.session)

        return redirect(reverse_lazy("pages:index"))


class AlpinePageView(TemplateView):
    template_name: str = "pages/alpine.html"


class QRCodePageView(TemplateView):
    template_name: str = "pages/qrcode.html"


class StyleGuideView(TemplateView):
    template_name = "pages/styleguide.html"


@csrf_exempt
def dummy_response(request):
    if request.method == "POST":
        return HttpResponse("POST: I am alive 🌳")
    else:
        q = request.GET.get("q")
        sleep = request.GET.get("sleep")

        if q:
            return HttpResponse(f"🔎 searching for {q}...")

        if sleep:
            time.sleep(int(sleep))
            return HttpResponse("😴 slept for %s seconds" % sleep)


def get_time(request):
    now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    return HttpResponse(now)
