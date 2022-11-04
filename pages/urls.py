from django.urls import path

from . import views

app_name = "pages"


urlpatterns = [
    path("", views.DashboardPageView.as_view(), name="home"),
    path("base/", views.BasePageView.as_view(), name="base"),
]
