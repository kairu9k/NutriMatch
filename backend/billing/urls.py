from django.urls import path

from .views import InitiatePaymentView, PayMongoWebhookView

urlpatterns = [
    path("client/invoices/<int:invoice_id>/pay/", InitiatePaymentView.as_view(), name="initiate_payment"),
]

webhook_urlpatterns = [
    path("webhooks/paymongo/", PayMongoWebhookView.as_view(), name="paymongo_webhook"),
]
