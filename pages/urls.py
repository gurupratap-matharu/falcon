from django.urls import path

from . import views

app_name = "pages"


urlpatterns = [
    path("", views.DashboardPageView.as_view(), name="home"),
]
