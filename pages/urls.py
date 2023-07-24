from django.urls import path

from . import views

app_name = "pages"


urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("about/", views.AboutPageView.as_view(), name="about"),
    path("terms/", views.TermsPageView.as_view(), name="terms"),
    path("privacy/", views.PrivacyPageView.as_view(), name="privacy"),
    path("contact/", views.ContactPageView.as_view(), name="contact"),
    path("feedback/", views.FeedbackPageView.as_view(), name="feedback"),
    path("favicon.ico", views.favicon),
    path("landing/", views.LandingPageView.as_view(), name="landing"),
    path("base/", views.BasePageView.as_view(), name="base"),  # TODO: Veer remove this!
    path(
        "base-hero/",
        views.BaseHeroPageView.as_view(),
        name="base-hero",
    ),  # TODO: Veer remove this!
    path("profile/<str:slug>/", views.PublicProfilePageView.as_view(), name="profile"),
    path("index/", views.IndexPageView.as_view(), name="index"),
    path("alpine/", views.AlpinePageView.as_view(), name="alpine"),
    path("dummy/", views.dummy_response, name="dummy"),
    path("time/", views.get_time, name="time"),
]
