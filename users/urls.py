from django.urls import path

from . import views

app_name = "users"


urlpatterns = [
    path("", views.ProfilePageView.as_view(), name="profile"),
    path("profile/", views.ProfileEditView.as_view(), name="profile-edit"),
    path("delete/", views.AccountDeleteView.as_view(), name="delete"),
]
