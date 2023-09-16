from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from companies.sitemaps import CompanySitemap
from pages.sitemaps import StaticViewSitemap
from trips.sitemaps import LocationSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "companies": CompanySitemap,
    "locations": LocationSitemap,
}


urlpatterns = [
    # Django admin
    path("private/", admin.site.urls),
    # Set language
    path("i18n/", include("django.conf.urls.i18n")),
    # User management
    path("accounts/", include("allauth.urls")),
    path("account/", include("users.urls")),
    # third party apps
    path("captcha/", include("captcha.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
    # Local apps
    path("trips/", include("trips.urls")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payments/", include("payments.urls")),
    path("companies/", include("companies.urls")),
    path("coupons/", include("coupons.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    from django.views.generic import TemplateView

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Add routes to test error templates
    urlpatterns += [
        path("test404/", TemplateView.as_view(template_name="404.html")),
        path("test500/", TemplateView.as_view(template_name="500.html")),
    ]
