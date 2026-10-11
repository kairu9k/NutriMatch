"""Per-patient care facts shared by the RND dashboard and My Patients:
meal-log adherence, progress, NCP / meal-plan stage and the "needs
attention" rules — computed once, in batches, so both pages agree.
Philippine time throughout."""

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

# "Patients needing attention" rules — simple and explainable on purpose.
NO_LOG_DAYS = 3          # no meal logged for this many days while on a plan
LOW_ADHERENCE = 50       # % over the last 7 days (with at least MIN_PLANNED meals planned)
MIN_PLANNED = 4
HIGH_NRS = 3             # NRS-2002 ≥ 3 = at nutritional risk
WEIGHT_JUMP_KG = Decimal("2")  # change between the last two progress records
STALE_DRAFT_DAYS = 3
ADHERENCE_GOAL = 80

LOG_SCORE = {"followed": 1.0, "partially_followed": 0.5, "not_followed": 0.0}
LEVEL_ORDER = {"critical": 0, "warning": 1, "info": 2}


def ph_tz():
    from .serializers import PH_TZ

    return PH_TZ


def person(u):
    return {"id": u.id, "name": u.full_name, "first_name": u.first_name, "profile_photo": u.profile_photo}


def _dow(d):
    return (d.weekday() + 1) % 7  # Sunday=0, like the app


class CareData:
    """Batched care facts for a set of one RND's relationships."""

    def __init__(self, rels, now=None):
        from clinical.models import NcpRecord, PreConsultationScreening, ProgressRecord
        from nutrition.models import MealLog, MealPlan, MealPlanMeal

        self.now = now or timezone.now()
        self.ph = ph_tz()
        self.today = self.now.astimezone(self.ph).date()
        self.rels = list(rels)
        rel_ids = [r.id for r in self.rels]
        client_ids = [r.client_id for r in self.rels]

        self.ncp = defaultdict(list)  # newest first
        for rec in NcpRecord.objects.filter(relationship_id__in=rel_ids).order_by("-created_at"):
            self.ncp[rec.relationship_id].append(rec)

        self.plans = defaultdict(list)  # newest first
        for p in MealPlan.objects.filter(relationship_id__in=rel_ids).order_by("-created_at"):
            self.plans[p.relationship_id].append(p)
        self.active_plans = {rid: next((p for p in ps if p.status == "active"), None) for rid, ps in self.plans.items()}
        self.active_plans = {rid: p for rid, p in self.active_plans.items() if p}

        self.meals = list(MealPlanMeal.objects.filter(meal_plan__in=self.active_plans.values()).select_related("meal_plan"))
        logs = MealLog.objects.filter(meal_plan_meal__in=self.meals, log_date__gte=self.today - timedelta(days=13),
                                      log_date__lte=self.today)
        self.log_map = {(lg.meal_plan_meal_id, lg.log_date): lg for lg in logs}
        self.last_log = {}
        for rid, log_date in (MealLog.objects.filter(meal_plan_meal__meal_plan__relationship_id__in=rel_ids)
                              .order_by("log_date").values_list("meal_plan_meal__meal_plan__relationship_id", "log_date")):
            self.last_log[rid] = log_date

        self.screenings = {}
        for s in PreConsultationScreening.objects.filter(client_id__in=client_ids).order_by("-created_at"):
            self.screenings.setdefault(s.client_id, s)

        self.progress = defaultdict(list)  # oldest first
        for pr in ProgressRecord.objects.filter(relationship_id__in=rel_ids).order_by("record_date", "created_at"):
            self.progress[pr.relationship_id].append(pr)

    # ------------------------------------------------------------ adherence
    def day_stats(self, d, rel_id=None):
        """(planned, logged, score) for one day — only meals whose time has passed count today."""
        planned = logged = 0
        score = 0.0
        for m in self.meals:
            plan = m.meal_plan
            if rel_id is not None and plan.relationship_id != rel_id:
                continue
            if m.day_of_week is not None and m.day_of_week != _dow(d):
                continue
            if d < (plan.sent_at or plan.created_at).astimezone(self.ph).date():
                continue
            if d == self.today and m.scheduled_time and datetime.combine(d, m.scheduled_time, tzinfo=self.ph) > self.now:
                continue
            planned += 1
            lg = self.log_map.get((m.id, d))
            if lg:
                logged += 1
                score += LOG_SCORE.get(lg.status, 0)
        return planned, logged, score

    def window(self, days_back_start, rel_id=None):
        planned = logged = 0
        score = 0.0
        for i in range(days_back_start, days_back_start + 7):
            p, lg, s = self.day_stats(self.today - timedelta(days=i), rel_id)
            planned += p
            logged += lg
            score += s
        return planned, logged, score

    def adherence(self, rel_id):
        """Last 7 days for one patient, or None when they have no active plan."""
        if rel_id not in self.active_plans:
            return None
        p, lg, s = self.window(0, rel_id)
        return {"pct": round(s / p * 100) if p else None, "planned": p, "logged": lg}

    # ------------------------------------------------------------ progress
    def weights(self, rel_id):
        return [p for p in self.progress.get(rel_id, []) if p.weight_kg is not None]

    def progress_summary(self, rel):
        from clinical.services import classify_bmi_asia_pacific

        recs = self.weights(rel.id)
        s = self.screenings.get(rel.client_id)
        start = s.weight_kg if s and s.weight_kg is not None else (recs[0].weight_kg if recs else None)
        latest = recs[-1].weight_kg if recs else None
        bmis = [p.bmi for p in self.progress.get(rel.id, []) if p.bmi is not None]
        bmi = bmis[-1] if bmis else (s.bmi if s else None)
        return {
            "latest_weight_kg": latest if latest is not None else start,
            "weight_change_kg": round(latest - start, 1) if latest is not None and start is not None and recs else None,
            "bmi": bmi,
            "bmi_class": classify_bmi_asia_pacific(bmi) if bmi is not None else None,
            "records": len(recs),
        }

    # ------------------------------------------------------------ care stage
    def stage(self, rel):
        """Where the patient is in the care process, plus the RND's next step."""
        recs = self.ncp.get(rel.id, [])
        draft = next((r for r in recs if r.status == "draft"), None)
        finalized = [r for r in recs if r.status == "completed"]
        plans = self.plans.get(rel.id, [])
        active_plan = self.active_plans.get(rel.id)
        draft_plan = next((p for p in plans if p.status == "draft"), None)
        has_intervention = bool(finalized and (finalized[0].diet_prescription or "").strip()) or \
            bool(recs and (recs[0].diet_prescription or "").strip())
        stage = {
            "screening": rel.client_id in self.screenings,
            "ncp": "draft" if draft and not finalized else ("done" if finalized else "none"),
            "meal_plan": "active" if active_plan else ("draft" if draft_plan else "none"),
            "ncp_draft": bool(draft),
            "follow_up": len(finalized) > 1,
            "ncp_count": len(finalized),
        }
        rid = rel.id
        if rel.status == "pending":
            step = ("review_booking", "Review booking", "/appointments")
        elif rel.status == "discharged":
            step = ("view", "View record", f"/client-detail/{rid}")
        elif draft:
            step = ("finish_ncp", "Finish NCP draft", f"/client-detail/{rid}?tab=ncp")
        elif not finalized:
            step = ("start_ncp", "Start NCP record", f"/client-detail/{rid}?tab=ncp")
        elif has_intervention and not active_plan:
            step = ("send_plan", "Send meal plan", f"/meal-planning?relationship={rid}") if draft_plan else \
                ("create_plan", "Create meal plan", f"/meal-planning?relationship={rid}")
        else:
            step = ("open", "Open chart", f"/client-detail/{rid}")
        stage["next_step"] = {"key": step[0], "label": step[1], "link": step[2]}
        return stage

    # ------------------------------------------------------------ attention
    def alerts(self, rel):
        """The dashboard's attention rules for one active patient, most urgent first."""
        if rel.status != "active":
            return []
        out = []
        c = rel.client
        plan = self.active_plans.get(rel.id)
        if plan:
            sent = (plan.sent_at or plan.created_at).astimezone(self.ph).date()
            last = self.last_log.get(rel.id)
            days_quiet = (self.today - max(last, sent)).days if last else (self.today - sent).days
            if days_quiet >= NO_LOG_DAYS:
                out.append({"level": "warning", "kind": "no_logs", "title": f"No meals logged in {days_quiet} days",
                            "detail": "They're on a meal plan but haven't logged anything — a quick message can help.",
                            "action": "Message", "link": f"/messages?relationship={rel.id}"})
            else:
                a = self.adherence(rel.id)
                if a and a["pct"] is not None and a["planned"] >= MIN_PLANNED and a["pct"] < LOW_ADHERENCE:
                    out.append({"level": "warning", "kind": "low_adherence", "title": f"Meal-plan adherence {a['pct']}% this week",
                                "detail": "Below 50% over the last 7 days. The plan may need adjusting.",
                                "action": "Open patient", "link": f"/client-detail/{rel.id}"})
        s = self.screenings.get(c.id)
        finalized = any(r.status == "completed" for r in self.ncp.get(rel.id, []))
        if s and s.nrs_score is not None and s.nrs_score >= HIGH_NRS and not finalized:
            out.append({"level": "critical", "kind": "nrs", "title": f"At nutritional risk (NRS-2002 score {s.nrs_score})",
                        "detail": "No completed NCP assessment yet.", "action": "Start NCP record",
                        "link": f"/client-detail/{rel.id}?tab=ncp"})
        recs = self.weights(rel.id)
        if len(recs) >= 2:
            change = recs[-1].weight_kg - recs[-2].weight_kg
            if abs(change) >= WEIGHT_JUMP_KG:
                out.append({"level": "warning", "kind": "weight",
                            "title": f"Weight {'up' if change > 0 else 'down'} {abs(change):.1f} kg since the last record",
                            "detail": f"{recs[-2].weight_kg} → {recs[-1].weight_kg} kg.", "action": "Open patient",
                            "link": f"/client-detail/{rel.id}"})
        for d in self.ncp.get(rel.id, []):
            age = (self.now - d.updated_at).days
            if d.status == "draft" and age >= STALE_DRAFT_DAYS:
                out.append({"level": "info", "kind": "stale_draft", "title": f"NCP draft untouched for {age} days",
                            "detail": "Finish it so it's finalized in the patient's record.", "action": "Continue",
                            "link": f"/client-detail/{rel.id}?tab=ncp"})
        for a in out:
            a["client"] = person(c)
            a["relationship_id"] = rel.id
        out.sort(key=lambda a: LEVEL_ORDER[a["level"]])
        return out
