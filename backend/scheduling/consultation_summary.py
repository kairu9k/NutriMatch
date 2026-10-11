"""Consultation summary for a completed visit (proposal: "consultation
summaries and progress reports after each session").

Built live from the visit's own records, so it reflects the NCP record once
the RND finalizes it:
  - measurements: the NCP record linked to this consultation, else the
    progress record from the visit date, else the latest earlier one;
  - change since the previous visit's weight (or the screening);
  - diagnosis (PES), prescription, targets, advice (intervention notes) and
    goal status from the linked NCP record;
  - the meal plan in effect and the next booked consultation.

Audience rules: the client sees NCP content only once it's FINALIZED and
never RND-only notes (assessment/lab/monitoring notes, private progress
notes); the RND also sees drafts, flagged as such.
  GET /api/rnd/appointments/<id>/summary/
  GET /api/client/appointments/<id>/summary/
"""

from datetime import timedelta

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd

from .models import Appointment


def _num(v):
    return float(v) if v is not None else None


def build_consultation_summary(appt, audience):
    from clinical.models import NcpRecord, PreConsultationScreening, ProgressRecord
    from clinical.services import classify_bmi_asia_pacific
    from nutrition.models import MealPlan

    from .patient_insights import ph_tz

    ph = ph_tz()
    rel = appt.relationship
    rnd, client = rel.rnd, rel.client
    visit_day = appt.scheduled_at.astimezone(ph).date()
    profile = getattr(rnd, "rnd_profile", None)

    ncp = NcpRecord.objects.filter(appointment=appt).order_by("-created_at").first()
    if ncp is None:  # older records weren't linked — the one written on the visit day
        ncp = NcpRecord.objects.filter(relationship=rel, encounter_date=visit_day).order_by("-created_at").first()
    ncp_visible = ncp is not None and (audience == "rnd" or ncp.status == NcpRecord.Status.COMPLETED)

    progress = (ProgressRecord.objects.filter(relationship=rel, record_date__lte=visit_day)
                .order_by("-record_date", "-created_at").first())
    m = {}
    if ncp_visible and (ncp.weight_kg or ncp.blood_pressure or ncp.blood_glucose or ncp.hba1c):
        src, m = "this visit's NCP record", {
            "weight_kg": _num(ncp.weight_kg), "height_cm": _num(ncp.height_cm), "bmi": _num(ncp.bmi),
            "blood_pressure": ncp.blood_pressure, "blood_glucose": _num(ncp.blood_glucose), "hba1c": _num(ncp.hba1c),
            "other": [{"label": r["label"], "value": r["value"], "unit": r.get("unit", "")} for r in (ncp.assessment_extra or [])],
        }
    elif progress:
        src, m = (f"progress record of {progress.record_date:%b} {progress.record_date.day}"), {
            "weight_kg": _num(progress.weight_kg), "bmi": _num(progress.bmi), "blood_pressure": progress.blood_pressure,
            "blood_glucose": _num(progress.blood_glucose), "hba1c": _num(progress.hba1c), "other": [],
        }
    else:
        src = None
    if m.get("bmi") is not None:
        m["bmi_class"] = classify_bmi_asia_pacific(m["bmi"])

    # weight change since the previous visit (progress before the visit day), else since the screening
    change = None
    if m.get("weight_kg") is not None:
        before = (ProgressRecord.objects.filter(relationship=rel, record_date__lt=visit_day, weight_kg__isnull=False)
                  .order_by("-record_date").first())
        if before:
            change = {"kg": round(m["weight_kg"] - float(before.weight_kg), 1), "since": before.record_date}
        else:
            s = PreConsultationScreening.objects.filter(client=client).order_by("created_at").first()
            if s:
                change = {"kg": round(m["weight_kg"] - float(s.weight_kg), 1), "since": s.created_at.astimezone(ph).date()}

    care = None
    if ncp_visible:
        care = {
            "status": ncp.status, "is_follow_up": ncp.is_follow_up(),
            "pes_problem": ncp.pes_problem, "pes_etiology": ncp.pes_etiology, "pes_signs": ncp.pes_signs,
            "diet_prescription": ncp.diet_prescription, "target_kcal": _num(ncp.target_kcal),
            "target_carb_g": _num(ncp.target_carb_g), "target_protein_g": _num(ncp.target_protein_g),
            "target_fat_g": _num(ncp.target_fat_g),
            "other_targets": [{"label": r["label"], "value": r["value"], "unit": r.get("unit", "")} for r in (ncp.intervention_extra or [])],
            "advice": ncp.intervention_notes,
            "goal_status": ncp.get_goal_status_display() if ncp.goal_status else None,
        }
        if audience == "rnd":
            from clinical.dietary import dietary_summary

            care.update({"assessment_notes": ncp.assessment_notes, "lab_notes": ncp.lab_notes, "monitoring_notes": ncp.monitoring_notes,
                         "dietary": dietary_summary(ncp)})

    plan = (MealPlan.objects.filter(relationship=rel, status=MealPlan.Status.ACTIVE).first()
            or (MealPlan.objects.filter(relationship=rel).exclude(status=MealPlan.Status.DRAFT).order_by("-sent_at").first()))
    nxt = (Appointment.objects.filter(relationship=rel, status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
                                      scheduled_at__gt=appt.scheduled_at).order_by("scheduled_at").first())

    return {
        "appointment": {
            "id": appt.id, "scheduled_at": appt.scheduled_at, "duration_minutes": appt.duration_minutes or 60,
            "type_label": appt.get_type_display(), "completed_at": appt.completed_at,
        },
        "rnd": {"name": rnd.full_name, "prc_license_number": getattr(profile, "prc_license_number", None),
                "specialization": getattr(profile, "specialization", None)},
        "client": {"name": client.full_name, "first_name": client.first_name},
        "measurements": m or None, "measurements_source": src, "weight_change": change,
        "care_plan": care,
        # the client is told when the RND hasn't finalized this visit's record yet
        "ncp_pending": ncp is not None and not ncp_visible,
        "no_ncp": ncp is None,
        "meal_plan": {"name": plan.name, "status": plan.status, "sent_at": plan.sent_at,
                      "target_kcal": _num(plan.target_kcal)} if plan else None,
        "next_appointment": {"scheduled_at": nxt.scheduled_at, "type_label": nxt.get_type_display(), "status": nxt.status} if nxt else None,
    }


def _completed(appt):
    if appt.status != Appointment.Status.COMPLETED:
        raise ValidationError({"detail": "A summary is available once the consultation is marked complete."})
    return appt


class RndConsultationSummaryView(APIView):
    permission_classes = [IsRnd]

    def get(self, request, pk):
        appt = get_object_or_404(Appointment.objects.select_related("relationship__rnd__rnd_profile", "relationship__client"),
                                 pk=pk, relationship__rnd=request.user)
        return Response(build_consultation_summary(_completed(appt), "rnd"))


class ClientConsultationSummaryView(APIView):
    permission_classes = [IsClient]

    def get(self, request, pk):
        appt = get_object_or_404(Appointment.objects.select_related("relationship__rnd__rnd_profile", "relationship__client"),
                                 pk=pk, relationship__client=request.user)
        return Response(build_consultation_summary(_completed(appt), "client"))
