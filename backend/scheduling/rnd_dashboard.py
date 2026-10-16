"""Everything the RND dashboard shows, from real data, in one request
(GET /api/rnd/dashboard/). Philippine time throughout."""

from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

from .patient_insights import ADHERENCE_GOAL, CareData, adherence_pct, person as _person, ph_tz

BMI_RANK = {"Normal": 0, "Overweight (At Risk)": 1, "Underweight": 1, "Obese I": 2, "Obese II": 3}


def build_dashboard(rnd, now=None):
    from billing.payouts import rnd_earnings
    from billing.services import appointment_invoice
    from clinical.models import NcpRecord
    from clinical.services import classify_bmi_asia_pacific
    from communication.models import Message
    from nutrition.models import MealPlan

    from .models import Appointment, Review, RndClientRelationship
    from .serializers import JOIN_EARLY_MINUTES, JOIN_LATE_MINUTES

    now = now or timezone.now()
    ph = ph_tz()
    today = now.astimezone(ph).date()
    day_start = datetime.combine(today, time.min, tzinfo=ph)

    rels = list(RndClientRelationship.objects.filter(rnd=rnd, status="active").select_related("client"))
    rel_ids = [r.id for r in rels]
    by_rel = {r.id: r for r in rels}

    # ---------------------------------------------------------------- schedule
    appts = (Appointment.objects.filter(relationship__rnd=rnd)
             .select_related("relationship__client").prefetch_related("invoices"))

    def appt_row(a):
        inv = appointment_invoice(a)
        end = a.scheduled_at + timedelta(minutes=a.duration_minutes or 60)
        return {
            "id": a.id, "scheduled_at": a.scheduled_at, "duration_minutes": a.duration_minutes or 60,
            "type": a.type, "type_label": a.get_type_display(), "status": a.status,
            "client": _person(a.relationship.client), "relationship_id": a.relationship_id,
            "payment": inv.status if inv else None,
            "join_opens_at": a.scheduled_at - timedelta(minutes=JOIN_EARLY_MINUTES),
            "join_closes_at": end + timedelta(minutes=JOIN_LATE_MINUTES),
            "video_session_url": a.video_session_url if a.type == "video" else None,
        }

    upcoming = [appt_row(a) for a in appts.filter(status__in=["pending", "confirmed"], scheduled_at__gte=now - timedelta(hours=2),
                                                   scheduled_at__lt=day_start + timedelta(days=8)).order_by("scheduled_at")]
    next_up = next((a for a in upcoming if a["status"] == "confirmed" and a["join_closes_at"] > now), None)
    requests = [appt_row(a) for a in appts.filter(status="pending", scheduled_at__gt=now).order_by("scheduled_at")]
    to_complete = appts.filter(status="confirmed", scheduled_at__lt=now - timedelta(minutes=60)).count()

    week_start = day_start - timedelta(days=today.weekday())  # Monday
    sessions_this_week = appts.filter(status__in=["confirmed", "completed"], scheduled_at__gte=week_start,
                                      scheduled_at__lt=week_start + timedelta(days=7)).count()

    # ---------------------------------------------------------------- clinical to-dos
    drafts = list(NcpRecord.objects.filter(relationship__rnd=rnd, status="draft").select_related("relationship__client"))
    latest_ncp = {}
    for rec in NcpRecord.objects.filter(relationship_id__in=rel_ids).order_by("relationship_id", "-created_at"):
        latest_ncp.setdefault(rec.relationship_id, rec)
    active_plans = {p.relationship_id: p for p in MealPlan.objects.filter(relationship_id__in=rel_ids, status="active")}
    need_plan = [by_rel[rid] for rid, rec in latest_ncp.items()
                 if (rec.diet_prescription or "").strip() and rid not in active_plans]
    unread = Message.objects.filter(relationship__rnd=rnd, is_read=False).exclude(sender=rnd).count()

    # ---------------------------------------------------------------- adherence + attention
    care = CareData(rels, now)
    screenings, progress = care.screenings, care.progress
    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        p, lg, s, w = care.day_stats(d)
        week.append({"date": d, "planned": p, "logged": lg, "waiting": w, "followed_pct": adherence_pct(p, s, w)})
    p7, l7, s7, w7 = care.window(0)
    p14, _, s14, w14 = care.window(7)
    adherence = {
        "days": week,
        "pct": adherence_pct(p7, s7, w7),
        "previous_pct": adherence_pct(p14, s14, w14),
        "planned": p7, "logged": l7, "waiting": w7, "goal": ADHERENCE_GOAL,
    }
    # Meal logs the RND still has to rate (any date), and the patient with the most.
    from nutrition.models import MealLog

    to_review = list(MealLog.objects.filter(
        status__isnull=True, meal_plan_meal__meal_plan__relationship__in=rels,
    ).values_list("meal_plan_meal__meal_plan__relationship_id", flat=True))
    # Lab results uploaded but not opened yet (any patient, even discharged).
    from clinical.models import LabResult

    labs_to_review = list(LabResult.objects.filter(relationship__rnd=rnd, reviewed_at__isnull=True)
                          .values_list("relationship_id", flat=True))
    alerts =[a for rel in rels for a in care.alerts(rel)]
    order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: order[a["level"]])

    # ---------------------------------------------------------------- outcomes
    changes, improved, compared = [], 0, 0
    for rel in rels:
        recs = [p for p in progress.get(rel.id, []) if p.weight_kg is not None]
        if len(recs) >= 2:
            changes.append(recs[-1].weight_kg - recs[0].weight_kg)
        bmis = [p.bmi for p in progress.get(rel.id, []) if p.bmi is not None]
        s = screenings.get(rel.client_id)
        start_bmi = s.bmi if s and s.bmi is not None else (bmis[0] if bmis else None)
        if start_bmi is not None and bmis:
            compared += 1
            if BMI_RANK.get(classify_bmi_asia_pacific(bmis[-1]), 9) < BMI_RANK.get(classify_bmi_asia_pacific(start_bmi), 9) \
                    or (bmis[-1] < start_bmi and classify_bmi_asia_pacific(start_bmi) != "Underweight"):
                improved += 1
    followups = NcpRecord.objects.filter(relationship__rnd=rnd, status="completed").exclude(goal_status__isnull=True).exclude(goal_status="")
    goal_counts = {k: followups.filter(goal_status=k).count() for k in ("met", "partially_met", "not_met", "ongoing")}
    outcomes = {
        "avg_weight_change_kg": round(sum(changes) / len(changes), 1) if changes else None,
        "weight_patients": len(changes),
        "bmi_improved": improved, "bmi_compared": compared,
        "goals": goal_counts,
    }

    # ---------------------------------------------------------------- money + reviews
    e = rnd_earnings(rnd, now)
    reviews = [{"rating": r.rating, "comment": r.comment, "client": f"{r.client.first_name} {r.client.last_name[:1]}.".strip(),
                "created_at": r.created_at}
               for r in Review.objects.filter(rnd=rnd, is_public=True).select_related("client").order_by("-created_at")[:3]]

    return {
        "generated_at": now,
        "next_up": next_up,
        "todo": {
            "requests": len(requests), "to_complete": to_complete, "ncp_drafts": len(drafts),
            "need_meal_plan": len(need_plan), "unread_messages": unread,
            "need_meal_plan_first": need_plan[0].id if need_plan else None,
            "meal_logs_to_review": len(to_review),
            "meal_logs_to_review_first": max(set(to_review), key=to_review.count) if to_review else None,
            "lab_results_to_review": len(labs_to_review),
            "lab_results_to_review_first": max(set(labs_to_review), key=labs_to_review.count) if labs_to_review else None,
        },
        "stats": {"active_patients": len(rels), "sessions_this_week": sessions_this_week},
        "schedule": upcoming,
        "requests": requests[:5],
        "adherence": adherence,
        "alerts": alerts[:8],
        "outcomes": outcomes,
        "earnings": {k: e[k] for k in ("pending", "posted", "paid_out", "next_payout_date", "eligible", "has_payout_account", "minimum_payout")},
        "reviews": reviews,
    }


class RndDashboardView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments()
        return Response(build_dashboard(request.user))
