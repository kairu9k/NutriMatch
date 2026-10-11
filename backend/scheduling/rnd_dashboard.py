"""Everything the RND dashboard shows, from real data, in one request
(GET /api/rnd/dashboard/). Philippine time throughout."""

from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

# "Patients needing attention" rules — simple and explainable on purpose.
NO_LOG_DAYS = 3          # no meal logged for this many days while on a plan
LOW_ADHERENCE = 50       # % over the last 7 days (with at least MIN_PLANNED meals planned)
MIN_PLANNED = 4
HIGH_NRS = 3             # NRS-2002 ≥ 3 = at nutritional risk
WEIGHT_JUMP_KG = Decimal("2")  # change between the last two progress records
STALE_DRAFT_DAYS = 3
ADHERENCE_GOAL = 80

LOG_SCORE = {"followed": 1.0, "partially_followed": 0.5, "not_followed": 0.0}
BMI_RANK = {"Normal": 0, "Overweight (At Risk)": 1, "Underweight": 1, "Obese I": 2, "Obese II": 3}


def _ph():
    from .serializers import PH_TZ

    return PH_TZ


def _person(u):
    return {"id": u.id, "name": u.full_name, "first_name": u.first_name, "profile_photo": u.profile_photo}


def _dow(d):
    return (d.weekday() + 1) % 7  # Sunday=0, like the app


def build_dashboard(rnd, now=None):
    from billing.payouts import rnd_earnings
    from billing.services import appointment_invoice
    from clinical.models import NcpRecord, PreConsultationScreening, ProgressRecord
    from clinical.services import classify_bmi_asia_pacific
    from communication.models import Message
    from nutrition.models import MealLog, MealPlan, MealPlanMeal

    from .models import Appointment, Review, RndClientRelationship
    from .serializers import JOIN_EARLY_MINUTES, JOIN_LATE_MINUTES

    now = now or timezone.now()
    ph = _ph()
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
    completed_ncp = set(NcpRecord.objects.filter(relationship_id__in=rel_ids, status="completed").values_list("relationship_id", flat=True))
    active_plans = {p.relationship_id: p for p in MealPlan.objects.filter(relationship_id__in=rel_ids, status="active")}
    need_plan = [by_rel[rid] for rid, rec in latest_ncp.items()
                 if (rec.diet_prescription or "").strip() and rid not in active_plans]
    unread = Message.objects.filter(relationship__rnd=rnd, is_read=False).exclude(sender=rnd).count()

    # ---------------------------------------------------------------- adherence (meal logs)
    meals = list(MealPlanMeal.objects.filter(meal_plan__in=active_plans.values()).select_related("meal_plan"))
    first_day = today - timedelta(days=13)
    logs = list(MealLog.objects.filter(meal_plan_meal__in=meals, log_date__gte=first_day, log_date__lte=today))
    log_map = {(lg.meal_plan_meal_id, lg.log_date): lg for lg in logs}
    last_log = {}
    for lg in MealLog.objects.filter(meal_plan_meal__meal_plan__relationship_id__in=rel_ids).order_by("log_date"):
        last_log[lg.meal_plan_meal.meal_plan.relationship_id] = lg.log_date

    def day_stats(d, rel_id=None):
        """(planned, logged, score) for one day — only meals whose time has passed count today."""
        planned = logged = 0
        score = 0.0
        for m in meals:
            plan = m.meal_plan
            if rel_id is not None and plan.relationship_id != rel_id:
                continue
            if m.day_of_week is not None and m.day_of_week != _dow(d):
                continue
            sent = plan.sent_at.astimezone(ph).date() if plan.sent_at else plan.created_at.astimezone(ph).date()
            if d < sent:
                continue
            if d == today and m.scheduled_time and datetime.combine(d, m.scheduled_time, tzinfo=ph) > now:
                continue
            planned += 1
            lg = log_map.get((m.id, d))
            if lg:
                logged += 1
                score += LOG_SCORE.get(lg.status, 0)
        return planned, logged, score

    def window(days_back_start, rel_id=None):
        planned = logged = 0
        score = 0.0
        for i in range(days_back_start, days_back_start + 7):
            p, lg, s = day_stats(today - timedelta(days=i), rel_id)
            planned += p
            logged += lg
            score += s
        return planned, logged, score

    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        p, lg, s = day_stats(d)
        week.append({"date": d, "planned": p, "logged": lg, "followed_pct": round(s / p * 100) if p else None})
    p7, l7, s7 = window(0)
    p14, _, s14 = window(7)
    adherence = {
        "days": week,
        "pct": round(s7 / p7 * 100) if p7 else None,
        "previous_pct": round(s14 / p14 * 100) if p14 else None,
        "planned": p7, "logged": l7, "goal": ADHERENCE_GOAL,
    }

    # ---------------------------------------------------------------- patients needing attention
    alerts = []
    screenings = {}
    for s in PreConsultationScreening.objects.filter(client__in=[r.client for r in rels]).order_by("client_id", "-created_at"):
        screenings.setdefault(s.client_id, s)
    progress = defaultdict(list)
    for pr in ProgressRecord.objects.filter(relationship_id__in=rel_ids).order_by("record_date"):
        progress[pr.relationship_id].append(pr)

    for rel in rels:
        c = rel.client
        plan = active_plans.get(rel.id)
        if plan:
            sent = (plan.sent_at or plan.created_at).astimezone(ph).date()
            last = last_log.get(rel.id)
            days_quiet = (today - max(last, sent)).days if last else (today - sent).days
            if days_quiet >= NO_LOG_DAYS:
                alerts.append({"level": "warning", "kind": "no_logs", "client": _person(c), "relationship_id": rel.id,
                               "title": f"No meals logged in {days_quiet} days",
                               "detail": "They're on a meal plan but haven't logged anything — a quick message can help.",
                               "action": "Message", "link": f"/messages?relationship={rel.id}"})
            else:
                pp, _, ps = window(0, rel.id)
                pct = round(ps / pp * 100) if pp else None
                if pct is not None and pp >= MIN_PLANNED and pct < LOW_ADHERENCE:
                    alerts.append({"level": "warning", "kind": "low_adherence", "client": _person(c), "relationship_id": rel.id,
                                   "title": f"Meal-plan adherence {pct}% this week",
                                   "detail": "Below 50% over the last 7 days. The plan may need adjusting.",
                                   "action": "Open patient", "link": f"/client-detail/{rel.id}"})
        s = screenings.get(c.id)
        if s and s.nrs_score is not None and s.nrs_score >= HIGH_NRS and rel.id not in completed_ncp:
            alerts.append({"level": "critical", "kind": "nrs", "client": _person(c), "relationship_id": rel.id,
                           "title": f"At nutritional risk (NRS-2002 score {s.nrs_score})",
                           "detail": "No completed NCP assessment yet.", "action": "Start NCP record",
                           "link": f"/client-detail/{rel.id}?tab=ncp"})
        recs = [p for p in progress.get(rel.id, []) if p.weight_kg is not None]
        if len(recs) >= 2:
            change = recs[-1].weight_kg - recs[-2].weight_kg
            if abs(change) >= WEIGHT_JUMP_KG:
                alerts.append({"level": "warning", "kind": "weight", "client": _person(c), "relationship_id": rel.id,
                               "title": f"Weight {'up' if change > 0 else 'down'} {abs(change):.1f} kg since the last record",
                               "detail": f"{recs[-2].weight_kg} → {recs[-1].weight_kg} kg.", "action": "Open patient",
                               "link": f"/client-detail/{rel.id}"})
    for d in drafts:
        age = (now - d.updated_at).days
        if age >= STALE_DRAFT_DAYS:
            alerts.append({"level": "info", "kind": "stale_draft", "client": _person(d.relationship.client),
                           "relationship_id": d.relationship_id, "title": f"NCP draft untouched for {age} days",
                           "detail": "Finish it so it's finalized in the patient's record.", "action": "Continue",
                           "link": f"/client-detail/{d.relationship_id}?tab=ncp"})
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
