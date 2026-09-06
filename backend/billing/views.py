from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin, IsClient, IsRnd
from core.models import AuditLog

from .models import Invoice, PaymentTransaction
from .serializers import (
    AdminInvoiceListSerializer,
    InvoiceListSerializer,
    InvoiceSerializer,
    RndInvoiceListSerializer,
)
from .services import InvalidWebhookSignatureError, PayMongoService, PaymentGatewayError


class ClientInvoiceListView(generics.ListAPIView):
    """Client's own invoices, most recent first."""

    serializer_class = InvoiceListSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return Invoice.objects.filter(
            relationship__client=self.request.user
        ).select_related("appointment", "appointment__relationship__rnd").order_by("-created_at")


class RndInvoiceListView(generics.ListAPIView):
    """RND's own invoices (their share of billable sessions), most recent
    first — powers the Earnings page's summary cards, trend chart, and
    invoice table, all computed client-side from this one list."""

    serializer_class = RndInvoiceListSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return Invoice.objects.filter(
            relationship__rnd=self.request.user
        ).select_related("relationship__client", "appointment").order_by("-created_at")


class AdminInvoiceListView(generics.ListAPIView):
    """Platform-wide invoice list for BillingCommission.vue — transaction
    log and per-RND payout summary are both derived from this one list
    client-side, same pattern as RndInvoiceListView's Earnings page."""

    serializer_class = AdminInvoiceListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Invoice.objects.select_related(
            "relationship__client", "relationship__rnd"
        ).order_by("-created_at")


class InitiatePaymentView(APIView):
    """Client-initiated payment: creates a PayMongo payment link for an
    unpaid invoice belonging to the caller."""

    permission_classes = [IsClient]

    def post(self, request, invoice_id):
        invoice = get_object_or_404(
            Invoice.objects.filter(relationship__client=request.user, status=Invoice.Status.UNPAID),
            pk=invoice_id,
        )

        try:
            result = PayMongoService().create_payment_link(invoice)
        except PaymentGatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        invoice.payment_gateway = Invoice.PaymentGateway.PAYMONGO
        invoice.payment_url = result["payment_url"]
        invoice.gateway_reference_id = result["gateway_reference_id"]
        invoice.save(update_fields=["payment_gateway", "payment_url", "gateway_reference_id"])

        return Response(InvoiceSerializer(invoice).data)


class PayMongoWebhookView(APIView):
    """External callback — no Sanctum/JWT auth, signature validated inside.
    Must NOT sit behind IsAuthenticated; PayMongo calls this unauthenticated."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        signature = request.headers.get("Paymongo-Signature", "")

        try:
            event = PayMongoService().handle_webhook(request.body, signature)
        except InvalidWebhookSignatureError:
            return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)
        except PaymentGatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        reference_id = event["gateway_reference_id"]
        invoice = Invoice.objects.filter(gateway_reference_id=reference_id).first()
        if invoice is None:
            # Acknowledge with 200 regardless — an unmatched event is not the
            # sender's problem to retry, and PayMongo will keep retrying on
            # non-2xx responses.
            return Response(status=status.HTTP_200_OK)

        PaymentTransaction.objects.create(
            invoice=invoice,
            transaction_type=PaymentTransaction.TransactionType.PAYMENT,
            amount=invoice.amount,
            status=event["status"],
            gateway_payload=event["raw"],
            processed_at=timezone.now(),
        )

        if event["status"] == "success" and invoice.status != Invoice.Status.PAID:
            invoice.status = Invoice.Status.PAID
            invoice.paid_at = timezone.now()
            invoice.save(update_fields=["status", "paid_at"])

            AuditLog.objects.create(
                action="invoice.paid",
                table_name="invoices",
                record_id=invoice.id,
                new_values={"status": "paid", "gateway_reference_id": reference_id},
            )
        elif event["status"] == "failed":
            invoice.status = Invoice.Status.CANCELLED
            invoice.save(update_fields=["status"])
        elif event["status"] == "refunded":
            invoice.status = Invoice.Status.REFUNDED
            invoice.save(update_fields=["status"])

        return Response(status=status.HTTP_200_OK)
