from django.urls import path

from . import views

app_name = "pages"


urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("seats/", views.SeatsView.as_view(), name="seats"),
    path("order/", views.OrderView.as_view(), name="order"),
    path("payment/", views.PaymentView.as_view(), name="payment"),
    path(
        "payment/success/", views.PaymentSuccessView.as_view(), name="payment-success"
    ),
    path("payment/fail/", views.PaymentFailView.as_view(), name="payment-fail"),
    path("dashboard/", views.DashboardPageView.as_view(), name="dashboard"),
    path("about/", views.AboutPageView.as_view(), name="about"),
    path("terms/", views.TermsPageView.as_view(), name="terms"),
    path("privacy/", views.PrivacyPageView.as_view(), name="privacy"),
    path("contact/", views.ContactPageView.as_view(), name="contact"),
    path("feedback/", views.FeedbackPageView.as_view(), name="feedback"),
    path("favicon.ico", views.favicon),
    path("base/", views.BasePageView.as_view(), name="base"),  # TODO: Veer remove this!
    path(
        "base-hero/",
        views.BaseHeroPageView.as_view(),
        name="base-hero",
    ),  # TODO: Veer remove this!
    path("profile/<str:slug>/", views.PublicProfilePageView.as_view(), name="profile"),
]
