from django.views.generic import TemplateView


class DashboardPageView(TemplateView):
    template_name = "pages/dashboard.html"


class BasePageView(TemplateView):
    template_name = "layouts/base.html"
