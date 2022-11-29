from django.urls import path

from . import views

app_name = "users"


urlpatterns = [
    path("profile/", views.ProfilePageView.as_view(), name="profile"),
    path("delete/", views.AccountDeleteView.as_view(), name="delete"),
]
