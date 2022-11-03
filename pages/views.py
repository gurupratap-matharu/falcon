from django.views.generic import TemplateView


class DashboardPageView(TemplateView):
    template_name = "pages/dashboard.html"
