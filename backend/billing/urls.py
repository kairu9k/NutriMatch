from django.urls import path

from .views import (
    AdminInvoiceDetailView,
    AdminInvoiceListView,
    AdminMarkRefundedView,
    AdminPayoutListView,
    AdminPayoutRunView,
    AdminReleasePayoutView,
    RndEarningsView,
    RndPayoutAccountView,
    ClientInvoiceListView,
    ClientInvoiceSyncView,
    InitiatePaymentView,
    PayMongoWebhookView,
    RndInvoiceListView,
)

urlpatterns = [
    path("client/invoices/", ClientInvoiceListView.as_view(), name="client_invoice_list"),
    path("client/invoices/sync/", ClientInvoiceSyncView.as_view(), name="client_invoice_sync"),
    path("client/invoices/<int:invoice_id>/pay/", InitiatePaymentView.as_view(), name="initiate_payment"),
    path("rnd/invoices/", RndInvoiceListView.as_view(), name="rnd_invoice_list"),
    path("admin/invoices/", AdminInvoiceListView.as_view(), name="admin_invoice_list"),
    path("admin/invoices/<int:invoice_id>/", AdminInvoiceDetailView.as_view(), name="admin_invoice_detail"),
    path("admin/payouts/", AdminPayoutListView.as_view(), name="admin_payout_list"),
    path("admin/payouts/run/", AdminPayoutRunView.as_view(), name="admin_payout_run"),
    path("admin/payouts/release/<int:rnd_id>/", AdminReleasePayoutView.as_view(), name="admin_release_payout"),
    path("rnd/payout-account/", RndPayoutAccountView.as_view(), name="rnd_payout_account"),
    path("rnd/earnings/", RndEarningsView.as_view(), name="rnd_earnings"),
    path("admin/invoices/<int:invoice_id>/mark-refunded/", AdminMarkRefundedView.as_view(), name="admin_mark_refunded"),
]

webhook_urlpatterns = [
    path("webhooks/paymongo/", PayMongoWebhookView.as_view(), name="paymongo_webhook"),
]
