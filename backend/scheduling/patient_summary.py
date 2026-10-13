"""Client Detail (GET /api/rnd/relationships/<id>/summary/): everything an
RND needs about one patient before or during a consultation, in one request —
the My Patients row plus screening, current care plan, meal plan + logs,
progress records and consultations."""

from datetime import timedelta

from django.http import Http404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

from .patient_insights import adherence_pct, ph_tz
from .patient_list import build_patient_rows

ADHERENCE_DAYS = 14
RECENT_LOGS = 20


def _num(v):
    return float(v) if v is not None else None


def build_patient_summary(rnd, rel_id, now=None):
    from billing.services import appointment_invoice
    from clinical.models import NcpRecord
    from nutrition.models import MealLog, MealPlan

    from .models import Appointment
    from .serializers import JOIN_EARLY_MINUTES, JOIN_LATE_MINUTES

    now = now or timezone.now()
    rows, care = build_patient_rows(rnd, now, rel_id=rel_id)
    if not rows:
        raise Http404
    row = rows[0]
    rel = care.rels[0]
    c = rel.client
    health = getattr(c, "health_profile", None)
    today = now.astimezone(ph_tz()).date()

    s = care.screenings.get(c.id)
    screening = {
        "id": s.id, "date": s.created_at, "height_cm": _num(s.height_cm), "weight_kg": _num(s.weight_kg),
        "bmi": _num(s.bmi), "bmi_category": s.bmi_category, "bmr_kcal": _num(s.bmr_kcal), "tdee_kcal": _num(s.tdee_kcal),
        "activity_level": s.get_activity_level_display(), "nrs_score": s.nrs_score,
        "nrs_risk": s.get_nrs_risk_display() if s.nrs_risk else None, "symptoms": s.symptoms,
    } if s else None

    # current care plan = the latest finalized NCP record (a draft in progress is flagged separately)
    recs = care.ncp.get(rel.id, [])
    current = next((r for r in recs if r.status == NcpRecord.Status.COMPLETED), None)
    care_plan = {
        "id": current.id, "encounter_date": current.encounter_date, "is_follow_up": current.is_follow_up(),
        "pes_problem": current.pes_problem, "pes_etiology": current.pes_etiology, "pes_signs": current.pes_signs,
        "diet_prescription": current.diet_prescription, "target_kcal": _num(current.target_kcal),
        "target_protein_g": _num(current.target_protein_g), "target_carb_g": _num(current.target_carb_g),
        "target_fat_g": _num(current.target_fat_g), "goal_status": current.get_goal_status_display() if current.goal_status else None,
        "monitoring_notes": current.monitoring_notes,
    } if current else None
    draft = next((r for r in recs if r.status == NcpRecord.Status.DRAFT), None)

    plans = care.plans.get(rel.id, [])
    plan = care.active_plans.get(rel.id) or next((p for p in plans if p.status == MealPlan.Status.DRAFT), None)
    meal_plan = None
    if plan:
        meals = list(plan.meals.all())
        meal_plan = {
            "id": plan.id, "name": plan.name, "status": plan.status, "sent_at": plan.sent_at,
            "target_kcal": _num(plan.target_kcal), "target_protein_g": _num(plan.target_protein_g),
            "target_carb_g": _num(plan.target_carb_g), "target_fat_g": _num(plan.target_fat_g),
            "meals_per_week": len(meals) if any(m.day_of_week is not None for m in meals) else len(meals) * 7,
            "updated_at": plan.updated_at,
        }
    days = []
    for i in range(ADHERENCE_DAYS - 1, -1, -1):
        d = today - timedelta(days=i)
        p, lg, sc, w = care.day_stats(d, rel.id)
        days.append({"date": d, "planned": p, "logged": lg, "waiting": w, "followed_pct": adherence_pct(p, sc, w)})
    logs = [
        {"id": lg.id, "date": lg.log_date, "meal": lg.meal_plan_meal.get_meal_time_display(), "status": lg.status,
         "status_label": lg.status_label, "time_logged": lg.time_logged, "note": lg.reason_notes,
         "photo_url": lg.photo_url, "plan": lg.meal_plan_meal.meal_plan.name}
        for lg in MealLog.objects.filter(meal_plan_meal__meal_plan__relationship=rel)
        .select_related("meal_plan_meal__meal_plan").order_by("-log_date", "-created_at")[:RECENT_LOGS]
    ]

    progress = [
        {"id": p.id, "record_date": p.record_date, "weight_kg": _num(p.weight_kg), "bmi": _num(p.bmi),
         "blood_pressure": p.blood_pressure, "blood_glucose": _num(p.blood_glucose), "hba1c": _num(p.hba1c),
         "rnd_notes": p.rnd_notes, "client_notes": p.client_notes, "source": p.source, "created_at": p.created_at}
        for p in reversed(care.progress.get(rel.id, []))
    ]

    appointments = []
    for a in sorted(rel.appointments.all(), key=lambda a: a.scheduled_at, reverse=True):
        inv = appointment_invoice(a)
        end = a.scheduled_at + timedelta(minutes=a.duration_minutes or 60)
        appointments.append({
            "id": a.id, "scheduled_at": a.scheduled_at, "duration_minutes": a.duration_minutes or 60,
            "type": a.type, "type_label": a.get_type_display(), "status": a.status,
            "payment": inv.status if inv else None, "amount": _num(inv.amount) if inv else None,
            "notes": a.notes, "cancellation_reason": a.cancellation_reason,
            "join_opens_at": a.scheduled_at - timedelta(minutes=JOIN_EARLY_MINUTES),
            "join_closes_at": end + timedelta(minutes=JOIN_LATE_MINUTES),
            "upcoming": a.status in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED) and end > now,
        })

    return {
        "patient": row,
        "health": {
            "conditions": (health.medical_conditions if health else None) or [],
            "allergies": (health.allergies if health else None) or [],
            "dietary_restrictions": (health.dietary_restrictions if health else None) or [],
            "health_goals": (health.health_goals if health else None) or [],
            "religion": health.religion if health else None,
        },
        "screening": screening,
        "care_plan": care_plan,
        "ncp_draft_id": draft.id if draft else None,
        "meal_plan": meal_plan,
        "adherence_days": days,
        "recent_logs": logs,
        "progress": progress,
        "appointments": appointments,
    }


class RndPatientSummaryView(APIView):
    permission_classes = [IsRnd]

    def get(self, request, pk):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments(relationship_id=pk, relationship__rnd=request.user)
        return Response(build_patient_summary(request.user, pk))
