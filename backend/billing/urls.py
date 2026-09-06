from django.urls import path

from .views import ClientInvoiceListView, InitiatePaymentView, PayMongoWebhookView

urlpatterns = [
    path("client/invoices/", ClientInvoiceListView.as_view(), name="client_invoice_list"),
    path("client/invoices/<int:invoice_id>/pay/", InitiatePaymentView.as_view(), name="initiate_payment"),
]

webhook_urlpatterns = [
    path("webhooks/paymongo/", PayMongoWebhookView.as_view(), name="paymongo_webhook"),
]
