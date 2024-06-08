from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.OrderCreateView.as_view(), name="order_create"),
    path("<uuid:order_id>/cancel/", views.order_cancel, name="order_cancel"),
    path("<uuid:order_id>/invoice/", views.InvoiceView.as_view(), name="invoice"),
    path(
        "<uuid:order_id>/invoice/pdf/",
        views.InvoicePDFView.as_view(),
        name="invoice_pdf",
    ),
    path(
        "admin/invoice/<uuid:order_id>/pdf/",
        views.InvoicePDFView.as_view(),
        name="admin_invoice_pdf",
    ),
    path("<uuid:order_id>/ticket/", views.TicketView.as_view(), name="ticket"),
    path(
        "<uuid:order_id>/ticket/pdf/", views.TicketPDFView.as_view(), name="ticket_pdf"
    ),
]
