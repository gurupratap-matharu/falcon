from django.urls import path

from users.views import AccountDeleteView, AccountSettingsView, ProfilePageView

app_name = "users"


urlpatterns = [
    path("", ProfilePageView.as_view(), name="profile"),
    path("settings/", AccountSettingsView.as_view(), name="settings"),
    path("delete/", AccountDeleteView.as_view(), name="delete"),
]
