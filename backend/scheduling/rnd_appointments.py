"""RND Appointments page (GET /api/rnd/appointments/board/): every
consultation sorted into what the RND has to do with it —
requests to answer, upcoming, ended but not marked complete, and history —
with just the details each row needs. Philippine time throughout."""

from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

from .models import Appointment
from .patient_insights import person, ph_tz


def build_board(rnd, now=None):
    from billing.services import appointment_invoice
    from clinical.models import PreConsultationScreening

    from .serializers import JOIN_EARLY_MINUTES, JOIN_LATE_MINUTES

    now = now or timezone.now()
    ph = ph_tz()
    today = now.astimezone(ph).date()
    day_start = datetime.combine(today, time.min, tzinfo=ph)
    week_start = day_start - timedelta(days=today.weekday())

    appts = list(
        Appointment.objects.filter(relationship__rnd=rnd)
        .select_related("relationship__client", "relationship__client__health_profile")
        .prefetch_related("invoices")
        .order_by("scheduled_at")
    )
    client_ids = {a.relationship.client_id for a in appts}
    screenings = {}
    for s in PreConsultationScreening.objects.filter(client_id__in=client_ids).order_by("-created_at"):
        screenings.setdefault(s.client_id, s)
    completed_before = {}  # relationship -> earliest completed consultation time
    for a in appts:
        if a.status == Appointment.Status.COMPLETED:
            completed_before.setdefault(a.relationship_id, a.scheduled_at)
    clinic = getattr(getattr(rnd, "rnd_profile", None), "clinic_address", None)

    rows = []
    for a in appts:
        rel = a.relationship
        c = rel.client
        inv = appointment_invoice(a)
        minutes = a.duration_minutes or 60
        end = a.scheduled_at + timedelta(minutes=minutes)
        if a.status == Appointment.Status.PENDING:
            bucket = "requests"
        elif a.status == Appointment.Status.CONFIRMED:
            bucket = "upcoming" if end > now else "to_complete"
        else:
            bucket = "history"
        row = {
            "id": a.id, "bucket": bucket, "status": a.status,
            "scheduled_at": a.scheduled_at, "ends_at": end, "duration_minutes": minutes,
            "type": a.type, "type_label": a.get_type_display(),
            "client": person(c), "relationship_id": rel.id, "relationship_status": rel.status,
            "returning": rel.id in completed_before and completed_before[rel.id] < a.scheduled_at,
            "payment": {"status": inv.status, "amount": inv.amount} if inv else None,
            "notes": a.notes, "cancellation_reason": a.cancellation_reason, "completed_at": a.completed_at,
            "join_opens_at": a.scheduled_at - timedelta(minutes=JOIN_EARLY_MINUTES),
            "join_closes_at": end + timedelta(minutes=JOIN_LATE_MINUTES),
            "has_video_room": bool(a.video_session_url),
            "clinic_address": clinic if a.type == Appointment.Type.IN_PERSON else None,
        }
        if bucket == "requests":
            health = getattr(c, "health_profile", None)
            s = screenings.get(c.id)
            row["time_passed"] = a.scheduled_at <= now
            row["starts_in_hours"] = round((a.scheduled_at - now).total_seconds() / 3600, 1)
            row["screening"] = {
                "submitted": bool(s),
                "conditions": (health.medical_conditions if health else None) or [],
                "allergies": (health.allergies if health else None) or [],
                "bmi": float(s.bmi) if s and s.bmi is not None else None,
                "bmi_category": s.bmi_category if s else None,
                "nrs_score": s.nrs_score if s else None,
                "nrs_risk": s.get_nrs_risk_display() if s and s.nrs_risk else None,
            }
        rows.append(row)

    history = [r for r in rows if r["bucket"] == "history"]
    history.sort(key=lambda r: r["scheduled_at"], reverse=True)
    pick = lambda b: [r for r in rows if r["bucket"] == b]  # noqa: E731 — already in time order
    active = [a for a in appts if a.status in (Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED)]
    return {
        "summary": {
            "today": sum(1 for a in active if a.scheduled_at.astimezone(ph).date() == today),
            "this_week": sum(1 for a in active if week_start <= a.scheduled_at < week_start + timedelta(days=7)),
            "requests": len(pick("requests")),
            "to_complete": len(pick("to_complete")),
        },
        "requests": pick("requests"),
        "upcoming": pick("upcoming"),
        "to_complete": pick("to_complete"),
        "history": history,
    }


class RndAppointmentBoardView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments(relationship__rnd=request.user)
        return Response(build_board(request.user))
