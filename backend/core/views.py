from datetime import timedelta

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
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
        pending_verif = RndProfile.objects.filter(is_verified=False).count()
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
        })


class AdminAuditLogListView(generics.ListAPIView):
    """Read-only — AuditLog rows are append-only by design (RA 10173),
    there's deliberately no admin-facing write/purge endpoint here."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user").order_by("-created_at")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(action__icontains=search)

        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)

        return qs


class AdminSystemSettingListView(generics.ListAPIView):
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAdmin]
    queryset = SystemSetting.objects.all().order_by("key")


class AdminSystemSettingUpdateView(APIView):
    """Update one setting by key (not by numeric id — keys are the stable,
    human-meaningful identifier here, e.g. 'platform_commission_pct')."""

    permission_classes = [IsAdmin]

    def patch(self, request, key):
        setting = get_object_or_404(SystemSetting, key=key)
        value = request.data.get("value")
        if value is None:
            return Response({"value": "This field is required."}, status=400)
        setting.value = value
        setting.updated_by = request.user
        setting.save(update_fields=["value", "updated_by", "updated_at"])
        return Response(SystemSettingSerializer(setting).data)
