from django.contrib.sitemaps import Sitemap

from .models import Location, Trip


class LocationSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return Location.objects.all()


class TripSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Trip.future.active()

    def lastmod(self, obj):
        return obj.updated_on
