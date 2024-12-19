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
    path("sitemap/", views.SitemapPageView.as_view(), name="sitemap"),
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots"),
    path(
        "3520839d70e34eb79e009ddb5fedef3b.txt",
        views.IndexNow.as_view(),
        name="indexnow",
    ),
    path("favicon.ico", views.favicon),
    path("para-empresas/", views.LandingPageView.as_view(), name="landing"),
    path("ayuda/", views.HelpPageView.as_view(), name="help"),
    path("profile/<str:slug>/", views.PublicProfilePageView.as_view(), name="profile"),
    path("index/", views.IndexPageView.as_view(), name="index"),
    path("alpine/", views.AlpinePageView.as_view(), name="alpine"),
    path("qrcode/", views.QRCodePageView.as_view(), name="qrcode"),
    path("styleguide/", views.StyleGuideView.as_view(), name="styleguide"),
    path("dummy/", views.dummy_response, name="dummy"),
    path("time/", views.get_time, name="time"),
]
