from django.urls import path

from . import views

app_name = "pages"


urlpatterns = [
    path("", views.DashboardPageView.as_view(), name="home"),
    path("about/", views.AboutPageView.as_view(), name="about"),
    path("base/", views.BasePageView.as_view(), name="base"),  # TODO: Veer remove this!
]
