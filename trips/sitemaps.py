from django.contrib.sitemaps import Sitemap

from .models import Location


class LocationSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return Location.objects.all()
