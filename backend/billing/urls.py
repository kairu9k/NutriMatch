from django.urls import path

from .views import ClientInvoiceListView, InitiatePaymentView, PayMongoWebhookView, RndInvoiceListView

urlpatterns = [
    path("client/invoices/", ClientInvoiceListView.as_view(), name="client_invoice_list"),
    path("client/invoices/<int:invoice_id>/pay/", InitiatePaymentView.as_view(), name="initiate_payment"),
    path("rnd/invoices/", RndInvoiceListView.as_view(), name="rnd_invoice_list"),
]

webhook_urlpatterns = [
    path("webhooks/paymongo/", PayMongoWebhookView.as_view(), name="paymongo_webhook"),
]
