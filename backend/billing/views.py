from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin, IsClient, IsRnd

from .models import Invoice, PaymentTransaction
from .serializers import (
    AdminInvoiceDetailSerializer,
    AdminInvoiceListSerializer,
    InvoiceListSerializer,
    InvoiceSerializer,
    RndInvoiceListSerializer,
)
from .services import (
    InvalidWebhookSignatureError,
    PayMongoService,
    PaymentGatewayError,
    record_successful_payment,
)


class ClientInvoiceListView(generics.ListAPIView):
    """Client's own invoices, most recent first."""

    serializer_class = InvoiceListSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return (Invoice.objects.filter(relationship__client=self.request.user)
                .select_related("appointment", "relationship__rnd").prefetch_related("transactions")
                .order_by("-created_at"))


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
        from .services import expire_unpaid_appointments

        expire_unpaid_appointments()
        return Invoice.objects.select_related(
            "relationship__client", "relationship__rnd"
        ).prefetch_related("transactions").order_by("-created_at")


class AdminInvoiceDetailView(generics.RetrieveAPIView):
    """One invoice with its payment receipt — the Billing & Commission
    invoice overlay."""

    serializer_class = AdminInvoiceDetailSerializer
    permission_classes = [IsAdmin]
    lookup_url_kwarg = "invoice_id"

    def get_queryset(self):
        return Invoice.objects.select_related(
            "relationship__client", "relationship__rnd", "appointment"
        )


class InitiatePaymentView(APIView):
    """Client-initiated payment: creates a PayMongo payment link for an
    unpaid invoice belonging to the caller."""

    permission_classes = [IsClient]

    def post(self, request, invoice_id):
        from django.utils import timezone

        from .services import expire_unpaid_appointments

        expire_unpaid_appointments(relationship__client=request.user)
        invoice = get_object_or_404(
            Invoice.objects.filter(relationship__client=request.user, status=Invoice.Status.UNPAID),
            pk=invoice_id,
        )
        # Pay before the consultation: no paying for one that already started.
        appt = invoice.appointment
        if appt is not None and appt.status in ("confirmed", "pending") and appt.scheduled_at <= timezone.now():
            return Response({"detail": "This consultation has already started, so it can't be paid online."}, status=status.HTTP_400_BAD_REQUEST)

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

        if event["status"] == "success":
            record_successful_payment(
                invoice, reference_id, event["raw"], source="webhook", payment_method=event.get("payment_method")
            )
            return Response(status=status.HTTP_200_OK)

        PaymentTransaction.objects.create(
            invoice=invoice,
            transaction_type=PaymentTransaction.TransactionType.PAYMENT,
            amount=invoice.amount,
            status=event["status"],
            gateway_payload=event["raw"],
            processed_at=timezone.now(),
        )
        if event["status"] == "failed":
            invoice.status = Invoice.Status.CANCELLED
            invoice.save(update_fields=["status"])
        elif event["status"] == "refunded":
            invoice.status = Invoice.Status.REFUNDED
            invoice.save(update_fields=["status"])

        return Response(status=status.HTTP_200_OK)


class ClientInvoiceSyncView(APIView):
    """Checks the caller's unpaid PayMongo invoices directly with PayMongo and
    marks any that were paid — the fallback when the payment.paid webhook
    never arrived (webhook disabled, tunnel down). The Billing page calls this
    on load and when the client returns from the checkout tab."""

    permission_classes = [IsClient]

    def post(self, request):
        pending = Invoice.objects.filter(
            relationship__client=request.user,
            status=Invoice.Status.UNPAID,
            payment_gateway=Invoice.PaymentGateway.PAYMONGO,
        ).exclude(gateway_reference_id__isnull=True).exclude(gateway_reference_id="")

        service = PayMongoService()
        updated = []
        for invoice in pending:
            try:
                result = service.get_payment_status(invoice.gateway_reference_id)
            except PaymentGatewayError:
                continue
            if result["status"] == "success" and record_successful_payment(
                invoice, invoice.gateway_reference_id, result["raw"], source="status_check",
                payment_method=result.get("payment_method"),
            ):
                updated.append(invoice.id)

        # A refund PayMongo has completed since → Refunded on the client's page.
        from .refunds import sync_refunds_for

        refunded = sync_refunds_for(Invoice.objects.filter(
            relationship__client=request.user, status=Invoice.Status.REFUND_PENDING,
            payment_gateway=Invoice.PaymentGateway.PAYMONGO,
        ))
        return Response({"updated": updated + refunded})



class AdminMarkRefundedView(APIView):
    """Admin confirms a refund-pending invoice was refunded in PayMongo."""

    permission_classes = [IsAdmin]

    def post(self, request, invoice_id):
        from django.utils import timezone

        from communication.services import notify
        from core.models import AuditLog

        from .models import PaymentTransaction

        invoice = get_object_or_404(Invoice, pk=invoice_id)
        if invoice.status != Invoice.Status.REFUND_PENDING:
            return Response({"detail": "Only refund-pending invoices can be marked refunded."}, status=status.HTTP_400_BAD_REQUEST)

        # Paid through PayMongo → only PayMongo can say it's refunded
        # (2026-10-19: a click alone used to mark it, money or not).
        from .refunds import apply_confirmed_refund, invoice_payment_id, paymongo_status

        if invoice_payment_id(invoice):
            try:
                state = paymongo_status(invoice)
            except PaymentGatewayError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
            if not apply_confirmed_refund(invoice, state, request.user):
                tried = state["refunds"][-1] if state["refunds"] else None
                why = (f"PayMongo shows the last refund attempt ({tried['id']}) as {tried['status']}"
                       if tried else "PayMongo has no refund for this payment yet")
                return Response({"detail": f"Not refunded yet — {why}. Use Refund through PayMongo, "
                                           "or refund it in the PayMongo dashboard first.",
                                 "paymongo": state}, status=status.HTTP_409_CONFLICT)
            return Response({"id": invoice.id, "status": Invoice.Status.REFUNDED})

        reference = (request.data.get("reference") or "").strip()[:100]
        invoice.status = Invoice.Status.REFUNDED
        invoice.save(update_fields=["status"])
        PaymentTransaction.objects.create(
            invoice=invoice,
            transaction_type=PaymentTransaction.TransactionType.REFUND,
            amount=invoice.amount,
            status="success",
            gateway_payload={"source": "admin", "reference": reference},
            processed_at=timezone.now(),
        )
        AuditLog.objects.create(
            user=request.user, action="invoice.refunded", table_name="invoices", record_id=invoice.id,
            new_values={"status": "refunded", "reference": reference},
        )
        notify(
            recipient=invoice.relationship.client, notifiable_type="invoice", notifiable_id=invoice.id,
            subject="Refund completed",
            content=f"Your ₱{invoice.amount:,.2f} refund for INV-{invoice.id:04d} has been processed.",
        )
        return Response({"id": invoice.id, "status": invoice.status})




class AdminInvoicePayMongoView(APIView):
    """GET → what PayMongo says about this invoice's payment and refunds
    (the admin invoice pop-up's "Check with PayMongo"). A refund PayMongo has
    completed turns a refund-pending invoice Refunded."""

    permission_classes = [IsAdmin]

    def get(self, request, invoice_id):
        from .refunds import apply_confirmed_refund, paymongo_status

        invoice = get_object_or_404(Invoice, pk=invoice_id)
        try:
            state = paymongo_status(invoice)
        except PaymentGatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        if state["available"] and invoice.status == Invoice.Status.REFUND_PENDING:
            apply_confirmed_refund(invoice, state, request.user)
            invoice.refresh_from_db(fields=["status"])
        return Response({**state, "invoice_status": invoice.status})


class AdminInvoiceRefundView(APIView):
    """POST → refund a refund-pending invoice through PayMongo (in full,
    once). It becomes Refunded only when PayMongo reports the refund
    succeeded."""

    permission_classes = [IsAdmin]

    def post(self, request, invoice_id):
        from .refunds import RefundError, refund_through_paymongo

        invoice = get_object_or_404(Invoice, pk=invoice_id)
        try:
            state, refund = refund_through_paymongo(invoice, request.user)
        except RefundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        invoice.refresh_from_db(fields=["status"])
        return Response({**state, "invoice_status": invoice.status, "refund": refund})

# --------------------------------------------------------------- payouts
class RndPayoutAccountView(APIView):
    """The RND's own GCash/bank details (GET; PUT creates or replaces)."""

    permission_classes = [IsRnd]

    def get(self, request):
        from .models import RndPayoutAccount
        from .serializers import RndPayoutAccountSerializer

        account = RndPayoutAccount.objects.filter(rnd=request.user).first()
        return Response(RndPayoutAccountSerializer(account).data if account else None)

    def put(self, request):
        from core.models import AuditLog

        from .models import RndPayoutAccount
        from .serializers import RndPayoutAccountSerializer

        account = RndPayoutAccount.objects.filter(rnd=request.user).first()
        before = (account.method, account.account_name, account.account_number, account.bank_name) if account else None
        serializer = RndPayoutAccountSerializer(account, data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save(rnd=request.user)
        changed = before != (saved.method, saved.account_name, saved.account_number, saved.bank_name)
        if changed:
            saved.details_changed_at = timezone.now()
            saved.save(update_fields=["details_changed_at"])
        AuditLog.objects.create(
            user=request.user, action="payout_account.updated", table_name="rnd_payout_accounts",
            record_id=saved.id, new_values={"method": saved.method, "details_changed": changed},
        )
        return Response(RndPayoutAccountSerializer(saved).data)


class RndEarningsView(APIView):
    """Pending / Posted / Paid out + next payout day + history (RND Earnings tab)."""

    permission_classes = [IsRnd]

    def get(self, request):
        from .models import Payout
        from .payouts import rnd_earnings
        from .serializers import PayoutSerializer

        from django.utils import timezone

        from .payouts import rnd_statement

        data = rnd_earnings(request.user)
        data["payouts"] = PayoutSerializer(Payout.objects.filter(rnd=request.user).order_by("-released_at"), many=True).data
        data["statement"] = rnd_statement(request.user)
        from core.ph_time import ph_date, ph_today

        month = ph_today()
        data["this_month"] = {
            "gross": sum((r["amount"] for r in data["statement"] if r["paid_at"] and ph_date(r["paid_at"]).replace(day=1) == month.replace(day=1)
                          and r["state"] in ("pending", "posted", "paid_out")), 0),
            "share": sum((r["share"] for r in data["statement"] if r["paid_at"] and ph_date(r["paid_at"]).replace(day=1) == month.replace(day=1)
                          and r["state"] in ("pending", "posted", "paid_out")), 0),
        }
        account = getattr(request.user, "payout_account", None)
        data["payout_account"] = {
            "method": account.method, "method_label": account.get_method_display(), "bank_name": account.bank_name,
            "account_name": account.account_name, "account_number_last4": account.account_number[-4:],
        } if account else None
        return Response(data)


def _resend_allowed(key, seconds=120):
    """One resend every 2 minutes per item, so the button can't flood an inbox."""
    from django.core.cache import cache

    return cache.add(key, 1, seconds)


class ClientResendReceiptView(APIView):
    """Email the receipt again (the first one is sent automatically)."""

    permission_classes = [IsClient]

    def post(self, request, invoice_id):
        from .receipts import send_client_receipt

        invoice = get_object_or_404(
            Invoice.objects.select_related("relationship__client", "relationship__rnd", "appointment"),
            pk=invoice_id, relationship__client=request.user,
            status__in=[Invoice.Status.PAID, Invoice.Status.REFUND_PENDING, Invoice.Status.REFUNDED],
        )
        if not _resend_allowed(f"resend-receipt:{invoice.id}"):
            return Response({"detail": "We just sent it — check your inbox (and spam folder), or try again in a couple of minutes."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            send_client_receipt(invoice)
        except Exception:
            return Response({"detail": "Couldn't send the email right now. Please try again later."}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"detail": f"Receipt sent to {request.user.email}."})


def payout_detail(payout):
    """A payout with the consultations it covered (RND Earnings, admin History)."""
    from .payouts import rnd_share
    from .serializers import PayoutSerializer

    data = PayoutSerializer(payout).data
    data["invoices"] = [
        {"invoice_id": inv.id, "client_name": inv.relationship.client.full_name,
         "consultation_at": inv.appointment.scheduled_at if inv.appointment else None,
         "amount": inv.amount, "commission": inv.commission_amt, "share": rnd_share(inv)}
        for inv in payout.invoices.select_related("relationship__client", "appointment").order_by("appointment__scheduled_at")
    ]
    return data


class RndPayoutDetailView(APIView):
    """One payout with the consultations it covered (Earnings page)."""

    permission_classes = [IsRnd]

    def get(self, request, payout_id):
        from .models import Payout

        return Response(payout_detail(get_object_or_404(Payout, pk=payout_id, rnd=request.user)))


class AdminPayoutDetailView(APIView):
    """One payout as a slip for the admin's History tab."""

    permission_classes = [IsAdmin]

    def get(self, request, payout_id):
        from .models import Payout

        return Response(payout_detail(get_object_or_404(Payout.objects.select_related("rnd", "released_by"), pk=payout_id)))


class RndResendPayoutEmailView(APIView):
    permission_classes = [IsRnd]

    def post(self, request, payout_id):
        from .models import Payout
        from .payouts import send_payout_email

        payout = get_object_or_404(Payout, pk=payout_id, rnd=request.user)
        if not _resend_allowed(f"resend-payout:{payout.id}"):
            return Response({"detail": "We just sent it — check your inbox (and spam folder), or try again in a couple of minutes."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            send_payout_email(payout)
        except Exception:
            return Response({"detail": "Couldn't send the email right now. Please try again later."}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"detail": f"Payout email sent to {request.user.email}."})


class AdminPayoutRunView(APIView):
    """Every RND with earnings — balances, eligibility and payout details —
    for the admin's monthly payout run (payout day is the 5th)."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from accounts.models import User

        from .payouts import HOLD_DAYS, MIN_PAYOUT, PAYOUT_DAY, details_recently_changed, last_payout_day, next_payout_date, rnd_earnings

        rows = []
        for rnd in User.objects.filter(role="rnd").order_by("first_name"):
            data = rnd_earnings(rnd)
            if not (data["pending"] or data["posted"] or data["paid_out"]):
                continue
            account = getattr(rnd, "payout_account", None)
            run_day, nxt = data["run_date"], data["next_payout_date"]
            if data["eligible"]:
                reason = None
            elif account is None:
                reason = "No payout details yet"
            elif data["payable"] == 0 and data["posted"] > 0:
                reason = f"Cleared after {run_day:%b} {run_day.day}, paid on {nxt:%b} {nxt.day}"
            else:
                reason = f"Below the ₱{MIN_PAYOUT:,.0f} minimum, carries over"
            rows.append({
                "rnd_id": rnd.id,
                "rnd_name": rnd.full_name,
                "email": rnd.email,
                "profile_photo": rnd.profile_photo,
                "pending": data["pending"],
                "posted": data["posted"],
                # what this run can pay: posted on or before the last 5th
                "payable": data["payable"],
                "payable_count": sum(1 for i in data["items"] if i["payable"]),
                "paid_out": data["paid_out"],
                "posted_count": sum(1 for i in data["items"] if i["state"] == "posted"),
                "pending_count": sum(1 for i in data["items"] if i["state"] == "pending"),
                # when the next pending share turns Posted (completed + HOLD_DAYS)
                "next_posts_on": min((i["posts_on"] for i in data["items"] if i["state"] == "pending" and i["posts_on"]), default=None),
                "eligible": data["eligible"],
                "reason": reason,
                "payout_account": {
                    "method": account.method, "method_label": account.get_method_display(),
                    "account_name": account.account_name, "account_number": account.account_number,
                    "bank_name": account.bank_name,
                    "details_changed_at": account.details_changed_at,
                    "recently_changed": details_recently_changed(account),
                } if account else None,
            })
        from core.ph_time import ph_today

        today = ph_today()
        return Response({
            "next_payout_date": next_payout_date(today),
            "run_date": last_payout_day(today),
            "payout_day_reached": today.day >= PAYOUT_DAY,
            "minimum_payout": MIN_PAYOUT,
            "hold_days": HOLD_DAYS,
            "rows": rows,
            "due_total": sum((r["payable"] for r in rows if r["eligible"]), 0),
        })


class AdminRndBalanceView(APIView):
    """One RND's unpaid money for the Payouts board (read only): every
    consultation on hold or cleared, when it clears or cleared, and whether
    it belongs to the payout that can be paid now."""

    permission_classes = [IsAdmin]

    def get(self, request, rnd_id):
        from accounts.models import User

        from .payouts import rnd_earnings

        rnd = get_object_or_404(User, pk=rnd_id, role="rnd")
        data = rnd_earnings(rnd)
        data["items"] = [i for i in data["items"] if i["state"] in ("pending", "posted")]
        data["rnd"] = {"id": rnd.id, "name": rnd.full_name, "email": rnd.email, "profile_photo": rnd.profile_photo}
        return Response(data)


class AdminReleasePayoutView(APIView):
    """Admin records that they sent an RND's posted balance (with the
    GCash/bank reference)."""

    permission_classes = [IsAdmin]

    def post(self, request, rnd_id):
        from accounts.models import User

        from .payouts import PayoutError, release_payout
        from .serializers import PayoutSerializer

        rnd = get_object_or_404(User, pk=rnd_id, role="rnd")
        try:
            payout = release_payout(
                rnd, reference=request.data.get("reference"), released_by=request.user, notes=request.data.get("notes", ""),
                expected_amount=request.data.get("expected_amount"),
                details_confirmed=request.data.get("details_confirmed") is True,
            )
        except PayoutError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)


class AdminPayoutListView(generics.ListAPIView):
    """Payout history (optionally ?rnd=<id>)."""

    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        from .serializers import PayoutSerializer

        return PayoutSerializer

    def get_queryset(self):
        from .models import Payout

        qs = Payout.objects.select_related("rnd", "released_by")
        rnd = self.request.query_params.get("rnd")
        return qs.filter(rnd_id=rnd) if rnd else qs
