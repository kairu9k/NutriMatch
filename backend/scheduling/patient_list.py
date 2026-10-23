"""My Patients (GET /api/rnd/patients/): one row per care relationship with
where the patient is in their care, adherence, progress, schedule and the
same attention flags as the dashboard — all in one request."""

from django.db.models import Exists, OuterRef, Prefetch, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd
from accounts.validators import age_on

from .models import Appointment, RndClientRelationship
from .patient_insights import CareData, ph_tz


def meal_plan_summary(care, rel):
    """For the Meal Planning patient list: the current plan (active, else the
    newest draft), whether a plan can be made yet (an NCP record has its
    Intervention — same rule as Client Detail), and whether a newer finalized
    NCP record means the plan's targets may be out of date."""
    plans = care.plans.get(rel.id, [])
    plan = care.active_plans.get(rel.id) or next((p for p in plans if p.status == "draft"), None)
    recs = care.ncp.get(rel.id, [])
    ready = any((r.diet_prescription or "").strip() or r.target_kcal for r in recs)
    outdated = bool(plan and plan.status == "active" and plan.sent_at and any(
        r.status == "completed" and r.encounter_date > plan.sent_at.astimezone(care.ph).date() for r in recs))
    return {
        "ready": ready,
        "plan": {
            "id": plan.id, "name": plan.name, "status": plan.status, "sent_at": plan.sent_at,
            "updated_at": plan.updated_at, "target_kcal": float(plan.target_kcal) if plan.target_kcal is not None else None,
        } if plan else None,
        "outdated": outdated,
    }


def build_patient_rows(rnd, now=None, rel_id=None, care=None):
    """All the RND's patients, or just one (`rel_id`). Returns rows and the CareData used."""
    from billing.services import appointment_invoice
    from communication.models import Message

    now = now or timezone.now()
    today = now.astimezone(ph_tz()).date()
    # A client whose booking was cancelled, declined or left unconfirmed until
    # its time passed isn't a patient: pending care only shows while a request
    # is still ahead or a booking is confirmed. Reopened care (discharged
    # before) stays listed — they were a patient.
    waiting = Appointment.objects.filter(relationship=OuterRef("pk")).filter(
        Q(status=Appointment.Status.CONFIRMED)
        | Q(status=Appointment.Status.PENDING, scheduled_at__gt=now)
    )
    qs = RndClientRelationship.objects.filter(rnd=rnd).filter(
        ~Q(status=RndClientRelationship.Status.PENDING)
        | Q(discharge_reason__isnull=False) & ~Q(discharge_reason="")
        | Q(Exists(waiting))
    )
    if rel_id is not None:
        qs = qs.filter(pk=rel_id)
    rels = list(
        qs
        .select_related("client", "client__client_profile", "client__health_profile")
        .prefetch_related(Prefetch("appointments", queryset=Appointment.objects.prefetch_related("invoices").order_by("scheduled_at")))
        .order_by("-created_at")
    )
    care = care or CareData(rels, now)
    unread = {}
    for rid in (Message.objects.filter(relationship__in=rels, is_read=False, deleted_at__isnull=True)
                .exclude(sender=rnd).values_list("relationship_id", flat=True)):
        unread[rid] = unread.get(rid, 0) + 1
    from clinical.models import LabResult

    new_labs = {}
    for rid in LabResult.objects.filter(relationship__in=rels, reviewed_at__isnull=True).values_list("relationship_id", flat=True):
        new_labs[rid] = new_labs.get(rid, 0) + 1

    rows = []
    for rel in rels:
        c = rel.client
        profile = getattr(c, "client_profile", None)
        health = getattr(c, "health_profile", None)
        appts = list(rel.appointments.all())
        done = [a for a in appts if a.status == Appointment.Status.COMPLETED]
        upcoming = [a for a in appts if a.status in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED) and a.scheduled_at > now]
        nxt = upcoming[0] if upcoming else None
        nxt_invoice = appointment_invoice(nxt) if nxt else None
        conditions = (health.medical_conditions if health else None) or []
        rows.append({
            "id": rel.id,
            "status": rel.status,
            "created_at": rel.created_at,
            "started_at": rel.started_at,
            "ended_at": rel.ended_at,
            "discharge_reason": rel.discharge_reason,
            "client": {
                "id": c.id, "first_name": c.first_name, "last_name": c.last_name, "name": c.full_name,
                "profile_photo": c.profile_photo,
                "age": age_on(profile.date_of_birth, today) if profile and profile.date_of_birth else None,
                "sex": profile.sex if profile else None,
            },
            "condition": conditions[0] if conditions else None,
            "other_conditions": max(len(conditions) - 1, 0),
            "allergies": (health.allergies if health else None) or [],
            "stage": care.stage(rel),
            "adherence": care.adherence(rel.id),
            "progress": care.progress_summary(rel),
            "last_visit": max(done, key=lambda a: a.scheduled_at).scheduled_at if done else None,
            "next_appointment": {
                "id": nxt.id, "scheduled_at": nxt.scheduled_at, "type_label": nxt.get_type_display(), "status": nxt.status,
                "payment": nxt_invoice.status if nxt_invoice else None,
            } if nxt else None,
            "consultations": len(done),
            "unread_messages": unread.get(rel.id, 0),
            "new_lab_results": new_labs.get(rel.id, 0),
            "alerts": [{"level": a["level"], "kind": a["kind"], "title": a["title"], "link": a["link"], "action": a["action"]}
                       for a in care.alerts(rel)],
            "meal_plan": meal_plan_summary(care, rel),
        })
    return rows, care


class RndPatientListView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        from billing.services import expire_unpaid_appointments

        from .discharge_requests import process_due_discharge_requests

        expire_unpaid_appointments(relationship__rnd=request.user)
        process_due_discharge_requests(rnd=request.user)
        return Response(build_patient_rows(request.user)[0])
