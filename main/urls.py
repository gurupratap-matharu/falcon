"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from companies.sitemaps import CompanySitemap
from pages.sitemaps import StaticViewSitemap
from trips.sitemaps import LocationSitemap, TripSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "companies": CompanySitemap,
    "trips": TripSitemap,
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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
