from django.contrib.sitemaps import Sitemap

from .models import Company


class CompanySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Company.objects.all()

    def lastmod(self, obj):
        return obj.updated_at
