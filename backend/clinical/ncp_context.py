"""What the NCP form needs besides the record itself
(GET /api/rnd/relationships/<id>/ncp/context/): pre-fill values with where
each came from, the previous finalized record (carried into a follow-up and
shown in Monitoring), and the patient strip beside the form."""

from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd
from accounts.validators import age_on


def _num(v):
    return float(v) if v is not None else None


def build_ncp_context(rel, now=None):
    from nutrition.models import MealPlan
    from scheduling.models import Appointment
    from scheduling.patient_insights import CareData, ph_tz

    from .models import NcpRecord, PreConsultationScreening, ProgressRecord

    now = now or timezone.now()
    today = now.astimezone(ph_tz()).date()
    c = rel.client
    profile = getattr(c, "client_profile", None)
    health = getattr(c, "health_profile", None)
    screening = PreConsultationScreening.objects.filter(client=c).order_by("-created_at").first()
    progress = list(ProgressRecord.objects.filter(relationship=rel).order_by("-record_date", "-created_at"))
    finalized = list(NcpRecord.objects.filter(relationship=rel, status=NcpRecord.Status.COMPLETED).order_by("-encounter_date", "-created_at"))
    prev = finalized[0] if finalized else None

    # Pre-fill: the most recent value of each measurement, with its source.
    candidates = {f: [] for f in ("height_cm", "weight_kg", "blood_pressure", "blood_glucose", "hba1c")}
    for p in progress:
        for f in ("weight_kg", "blood_pressure", "blood_glucose", "hba1c"):
            if getattr(p, f) not in (None, ""):
                candidates[f].append((p.record_date, getattr(p, f), "progress record"))
    if screening:
        d = screening.created_at.astimezone(ph_tz()).date()
        candidates["height_cm"].append((d, screening.height_cm, "screening"))
        candidates["weight_kg"].append((d, screening.weight_kg, "screening"))
    for r in finalized:
        for f in candidates:
            if getattr(r, f) not in (None, ""):
                candidates[f].append((r.encounter_date, getattr(r, f), "previous NCP record"))
    prefill = {}
    for f, vals in candidates.items():
        if vals:
            d, v, src = max(vals, key=lambda x: x[0])
            prefill[f] = {"value": v if isinstance(v, str) else _num(v), "source": src, "date": d}

    previous = None
    if prev:
        latest_w = prefill.get("weight_kg", {}).get("value")
        previous = {
            "id": prev.id, "encounter_date": prev.encounter_date,
            "weight_kg": _num(prev.weight_kg), "bmi": _num(prev.bmi),
            "pes_problem": prev.pes_problem, "pes_etiology": prev.pes_etiology, "pes_signs": prev.pes_signs,
            "diet_prescription": prev.diet_prescription, "target_kcal": _num(prev.target_kcal),
            "target_protein_g": _num(prev.target_protein_g), "target_carb_g": _num(prev.target_carb_g),
            "target_fat_g": _num(prev.target_fat_g), "intervention_notes": prev.intervention_notes,
            "goal_status": prev.goal_status,
            "weight_change_kg": round(latest_w - float(prev.weight_kg), 1) if latest_w is not None and prev.weight_kg else None,
        }

    care = CareData([rel], now)
    plan = MealPlan.objects.filter(relationship=rel, status=MealPlan.Status.ACTIVE).first()

    # The consultation happening now (or today) — new records are linked to it.
    window = Appointment.objects.filter(relationship=rel, status=Appointment.Status.CONFIRMED,
                                        scheduled_at__gte=now - timedelta(hours=3), scheduled_at__lte=now + timedelta(hours=12)).order_by("scheduled_at").first()

    return {
        "is_follow_up": bool(finalized),
        "prefill": prefill,
        "previous": previous,
        "adherence": care.adherence(rel.id),
        "patient": {
            "name": c.full_name, "first_name": c.first_name,
            "age": age_on(profile.date_of_birth, today) if profile and profile.date_of_birth else None,
            "sex": profile.sex if profile else None,
            "conditions": (health.medical_conditions if health else None) or [],
            "allergies": (health.allergies if health else None) or [],
            "dietary_restrictions": (health.dietary_restrictions if health else None) or [],
            "health_goals": (health.health_goals if health else None) or [],
            "religion": health.religion if health else None,
        },
        "screening": {
            "date": screening.created_at, "bmi": _num(screening.bmi), "bmi_category": screening.bmi_category,
            "bmr_kcal": _num(screening.bmr_kcal), "tdee_kcal": _num(screening.tdee_kcal),
            "activity_level": screening.get_activity_level_display(), "nrs_score": screening.nrs_score,
            "nrs_risk": screening.get_nrs_risk_display() if screening.nrs_risk else None, "symptoms": screening.symptoms,
        } if screening else None,
        "meal_plan": {
            "name": plan.name, "target_kcal": _num(plan.target_kcal), "target_carb_g": _num(plan.target_carb_g),
            "target_protein_g": _num(plan.target_protein_g), "target_fat_g": _num(plan.target_fat_g),
        } if plan else None,
        "appointment_id": window.id if window else None,
    }


class NcpContextView(APIView):
    permission_classes = [IsRnd]

    def get(self, request, relationship_id):
        from scheduling.models import RndClientRelationship

        rel = get_object_or_404(
            RndClientRelationship.objects.select_related("client", "client__client_profile", "client__health_profile"),
            pk=relationship_id, rnd=request.user,
        )
        return Response(build_ncp_context(rel))
