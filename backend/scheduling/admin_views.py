"""Admin view of every appointment (Admin > Appointments): list with
filters, a summary for the tabs/dashboard, and cancelling on a user's
behalf. No video links here — the admin doesn't need the room."""

from datetime import date, datetime, time, timedelta

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin

from .models import Appointment
from .serializers import PH_TZ

# A booking request the RND hasn't answered for this long needs a nudge.
STALE_REQUEST_HOURS = 24


def _ph_day_start(value):
    try:
        return datetime.combine(date.fromisoformat(value), time.min, tzinfo=PH_TZ)
    except (TypeError, ValueError):
        return None


def _ph_today_bounds(now=None):
    now = now or timezone.now()
    start = datetime.combine(now.astimezone(PH_TZ).date(), time.min, tzinfo=PH_TZ)
    return start, start + timedelta(days=1)


class AdminAppointmentSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    rnd = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    type_label = serializers.CharField(source="get_type_display")

    class Meta:
        model = Appointment
        fields = [
            "id", "scheduled_at", "duration_minutes", "type", "type_label", "status", "client", "rnd", "payment",
            "cancellation_reason", "notes", "created_at", "updated_at", "completed_at",
        ]

    def _person(self, user):
        return {"id": user.id, "name": user.full_name, "email": user.email, "profile_photo": user.profile_photo}

    def get_client(self, obj):
        return self._person(obj.relationship.client)

    def get_rnd(self, obj):
        return self._person(obj.relationship.rnd)

    def get_payment(self, obj):
        invoices = getattr(obj, "_invoices", None)
        invoice = invoices[0] if invoices else None
        if invoice is None:
            return None
        return {"invoice_id": invoice.id, "status": invoice.status, "amount": str(invoice.amount), "paid_at": invoice.paid_at}


def admin_appointments():
    from billing.models import Invoice

    return Appointment.objects.select_related("relationship__client", "relationship__rnd").prefetch_related(
        Prefetch("invoices", queryset=Invoice.objects.order_by("-created_at"), to_attr="_invoices"),
    )


class AdminAppointmentPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class AdminAppointmentListView(generics.ListAPIView):
    """?view=upcoming|requests|past|cancelled|all, search (client/RND name or
    email), rnd, client, status, payment (paid|unpaid|refund_pending),
    date_from/date_to (YYYY-MM-DD, Philippine time). Upcoming soonest first,
    everything else newest first."""

    serializer_class = AdminAppointmentSerializer
    permission_classes = [IsAdmin]
    pagination_class = AdminAppointmentPagination
    filter_backends = []

    def get_queryset(self):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments()
        p = self.request.query_params
        qs = admin_appointments()
        now = timezone.now()
        view = p.get("view") or "upcoming"
        if view == "upcoming":
            qs = qs.filter(status__in=["pending", "confirmed"], scheduled_at__gte=now).order_by("scheduled_at")
        elif view == "requests":
            qs = qs.filter(status="pending", scheduled_at__gte=now).order_by("created_at")
        elif view == "past":
            # includes requests whose time passed without the RND confirming
            qs = qs.filter(Q(status="completed") | Q(status__in=["pending", "confirmed"], scheduled_at__lt=now)).order_by("-scheduled_at")
        elif view == "cancelled":
            qs = qs.filter(status="cancelled").order_by("-updated_at")
        else:
            qs = qs.order_by("-scheduled_at")

        search = (p.get("search") or "").strip()
        if search:
            q = Q(pk=int(search)) if search.isdigit() else Q()
            for part in search.split():
                for side in ("client", "rnd"):
                    q |= (Q(**{f"relationship__{side}__first_name__icontains": part})
                          | Q(**{f"relationship__{side}__last_name__icontains": part})
                          | Q(**{f"relationship__{side}__email__icontains": part}))
            qs = qs.filter(q)
        for key in ("rnd", "client"):
            value = p.get(key)
            if value and value.isdigit():
                qs = qs.filter(**{f"relationship__{key}_id": int(value)})
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        payment = p.get("payment")
        if payment == "unpaid":
            qs = qs.filter(invoices__status="unpaid").distinct()
        elif payment in ("paid", "refund_pending", "refunded"):
            qs = qs.filter(invoices__status=payment).distinct()
        start = _ph_day_start(p.get("date_from"))
        if start:
            qs = qs.filter(scheduled_at__gte=start)
        end = _ph_day_start(p.get("date_to"))
        if end:
            qs = qs.filter(scheduled_at__lt=end + timedelta(days=1))
        return qs


def appointment_summary(now=None):
    """Numbers for the Appointments tabs and the admin dashboard."""
    now = now or timezone.now()
    day_start, day_end = _ph_today_bounds(now)
    week_end = day_start + timedelta(days=7)
    active = Appointment.objects.filter(status__in=["pending", "confirmed"])
    return {
        "today": active.filter(scheduled_at__gte=day_start, scheduled_at__lt=day_end).count(),
        "next_7_days": active.filter(scheduled_at__gte=day_start, scheduled_at__lt=week_end).count(),
        "upcoming": active.filter(scheduled_at__gte=now).count(),
        "requests": Appointment.objects.filter(status="pending", scheduled_at__gte=now).count(),
        "expired_requests": Appointment.objects.filter(status="pending", scheduled_at__lt=now).count(),
        "stale_requests": Appointment.objects.filter(
            status="pending", created_at__lt=now - timedelta(hours=STALE_REQUEST_HOURS), scheduled_at__gte=now,
        ).count(),
        "unpaid_soon": Appointment.objects.filter(
            status="confirmed", scheduled_at__gte=now, scheduled_at__lt=now + timedelta(hours=24), invoices__status="unpaid",
        ).distinct().count(),
        "cancelled_7_days": Appointment.objects.filter(status="cancelled", updated_at__gte=now - timedelta(days=7)).count(),
        "completed_7_days": Appointment.objects.filter(status="completed", completed_at__gte=now - timedelta(days=7)).count(),
        "stale_request_hours": STALE_REQUEST_HOURS,
    }


class AdminAppointmentSummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments()
        return Response(appointment_summary())


class AdminAppointmentCancelView(APIView):
    """Cancel an upcoming appointment on a user's behalf (e.g. after a
    support request). Same money rules as the client/RND cancel: paid →
    refund pending, unpaid → voided. Both sides are notified; audit-logged."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from billing.services import settle_cancelled_appointment
        from communication.services import notify
        from core.models import AuditLog

        from .views import format_ph_datetime

        appointment = get_object_or_404(admin_appointments(), pk=pk)
        if appointment.status not in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED):
            return Response(
                {"detail": f"This appointment is already {appointment.get_status_display().lower()} and can't be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = (request.data.get("reason") or "").strip()
        if len(reason) < 10:
            return Response({"reason": ["Explain why in at least 10 characters — both the client and the RND will see this."]},
                            status=status.HTTP_400_BAD_REQUEST)
        reason = reason[:500]
        old_status = appointment.status
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancellation_reason = f"Cancelled by NutriMatch: {reason}"[:500]
        appointment.save(update_fields=["status", "cancellation_reason", "updated_at"])
        invoice = settle_cancelled_appointment(appointment)

        when = format_ph_datetime(appointment.scheduled_at)
        kind = appointment.get_type_display().lower()
        client, rnd = appointment.relationship.client, appointment.relationship.rnd
        notify(recipient=client, notifiable_type="appointment", notifiable_id=appointment.id, subject="Appointment cancelled",
               content=f"The NutriMatch team cancelled your {kind} consultation with RND {rnd.full_name} for {when}. Reason: {reason}")
        notify(recipient=rnd, notifiable_type="appointment", notifiable_id=appointment.id, subject="Appointment cancelled",
               content=f"The NutriMatch team cancelled your {kind} consultation with {client.full_name} for {when}. Reason: {reason}")
        from communication.reminders import _when
        from communication.sms import text_client

        text_client(client, f"NutriMatch cancelled your consultation with RND {rnd.full_name} on {_when(appointment.scheduled_at)}. "
                            "Open the app for details.")
        AuditLog.objects.create(
            user=request.user, action="appointment.cancelled", table_name="appointments", record_id=appointment.id,
            old_values={"status": old_status},
            new_values={"status": "cancelled", "reason": reason, "invoice_status": invoice.status if invoice else None},
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        appointment = admin_appointments().get(pk=pk)
        return Response(AdminAppointmentSerializer(appointment).data)
