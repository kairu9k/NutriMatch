from datetime import timedelta

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdmin
from billing.models import Invoice
from profiles.models import RndProfile
from scheduling.models import Appointment

from .models import AuditLog, SystemSetting
from .serializers import AuditLogSerializer, SystemSettingSerializer


class AdminPlatformStatsView(APIView):
    """Aggregate platform-wide numbers for the admin dashboard/reports/
    billing pages — all real, computed live, nothing hardcoded. No
    "platform uptime" here (that would need real infra monitoring this
    project doesn't have) — dropped rather than faked."""

    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - timedelta(days=30)

        active_rnds = RndProfile.objects.filter(is_verified=True, user__is_active=True).count()
        # Applications still awaiting a decision (not rejected / deactivated).
        pending_verif = RndProfile.objects.filter(review_status="pending", user__is_active=True).count()
        clients = User.objects.filter(role=User.Role.CLIENT, is_active=True).count()
        new_registrations = User.objects.filter(created_at__gte=thirty_days_ago).count()
        total_consultations = Appointment.objects.filter(status=Appointment.Status.COMPLETED).count()

        paid_this_month = Invoice.objects.filter(status=Invoice.Status.PAID, paid_at__gte=month_start)
        gross_revenue = paid_this_month.aggregate(total=Sum("amount"))["total"] or 0
        commissions = paid_this_month.aggregate(total=Sum("commission_amt"))["total"] or 0

        return Response({
            "active_rnds": active_rnds,
            "pending_verif": pending_verif,
            "clients": clients,
            "new_registrations": new_registrations,
            "total_consultations": total_consultations,
            "gross_revenue": gross_revenue,
            "commissions": commissions,
            **_admin_todo_counts(),
        })


def _admin_todo_counts():
    """Numbers for the admin dashboard's to-do banner."""
    from billing.payouts import next_payout_date, rnd_earnings
    from scheduling.admin_views import appointment_summary

    due_total = 0
    due_rnds = 0
    for rnd in User.objects.filter(role=User.Role.RND, rnd_profile__is_verified=True):
        data = rnd_earnings(rnd)
        if data["eligible"]:
            due_rnds += 1
            due_total += data["posted"]
    return {
        "refunds_pending": Invoice.objects.filter(status="refund_pending").count(),
        "unpaid_invoices": Invoice.objects.filter(status=Invoice.Status.UNPAID).count(),
        "payouts_due_count": due_rnds,
        "payouts_due_total": due_total,
        "next_payout_date": next_payout_date(timezone.localdate()),
        "appointments": appointment_summary(),
    }


class AuditLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class AdminAuditLogListView(generics.ListAPIView):
    """Read-only — AuditLog rows are append-only by design (RA 10173),
    there's deliberately no admin-facing write/purge endpoint here.
    Paged ({count, next, previous, results}); filters in core/audit.py."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    pagination_class = AuditLogPagination
    filter_backends = []

    def get_queryset(self):
        from .audit import filtered_audit_logs

        return filtered_audit_logs(self.request.query_params)


class AdminAuditLogActionsView(APIView):
    """Every event type with its count, for the Audit Logs filter."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from django.db.models import Count

        rows = AuditLog.objects.values("action").annotate(count=Count("id")).order_by("action")
        return Response(list(rows))


class AdminAuditLogExportView(APIView):
    """CSV of the filtered audit log. The export itself is audit-logged."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from django.http import HttpResponse

        from .audit import PH_TZ, audit_logs_csv, filtered_audit_logs

        qs = filtered_audit_logs(request.query_params)
        count = qs.count()
        body = audit_logs_csv(qs)
        filters = {k: v for k, v in request.query_params.items() if k in ("search", "action", "user", "date_from", "date_to", "scope") and v}
        AuditLog.objects.create(
            user=request.user, action="audit_log.exported", table_name="audit_logs",
            new_values={"rows": count, **filters}, ip_address=request.META.get("REMOTE_ADDR"),
        )
        stamp = timezone.now().astimezone(PH_TZ).strftime("%Y%m%d-%H%M")
        response = HttpResponse(body, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="nutrimatch-audit-log-{stamp}.csv"'
        return response


class AdminSystemSettingListView(generics.ListAPIView):
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAdmin]
    queryset = SystemSetting.objects.all().order_by("key")


class AdminSystemSettingUpdateView(APIView):
    """Update one setting by key (not by numeric id — keys are the stable,
    human-meaningful identifier here, e.g. 'platform_commission_pct')."""

    permission_classes = [IsAdmin]

    def patch(self, request, key):
        from decimal import Decimal, InvalidOperation

        setting = get_object_or_404(SystemSetting, key=key)
        value = request.data.get("value")
        if value is None or str(value).strip() == "":
            return Response({"value": "This field is required."}, status=400)
        value = str(value).strip()
        if key == "platform_commission_pct":
            try:
                pct = Decimal(value)
            except InvalidOperation:
                return Response({"value": "Enter a number, e.g. 10."}, status=400)
            if not Decimal("0") <= pct <= Decimal("50"):
                return Response({"value": "The commission must be between 0% and 50%."}, status=400)
            value = f"{pct:.2f}"
        old = setting.value
        setting.value = value
        setting.updated_by = request.user
        setting.save(update_fields=["value", "updated_by", "updated_at"])
        AuditLog.objects.create(user=request.user, action="setting.updated", table_name="system_settings",
                                record_id=setting.pk, old_values={key: old}, new_values={key: value})
        return Response(SystemSettingSerializer(setting).data)
