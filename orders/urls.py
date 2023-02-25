from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.OrderCreateView.as_view(), name="order_create"),
    path("<uuid:order_id>/ticket/", views.ticket, name="ticket"),
    path("<uuid:order_id>/ticket/pdf/", views.ticket_pdf, name="ticket_pdf"),
    # custom admin endpoints
    path(
        "admin/order/<uuid:order_id>/pdf/",
        views.admin_order_pdf,
        name="admin_order_pdf",
    ),
]
