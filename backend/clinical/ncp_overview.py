"""NCP Records page (GET /api/rnd/ncp/overview/) — view only: every NCP
record across the RND's patients, plus the worklist of who needs one.
Records are written and edited on the patient chart (and in the consultation
room), never here. Philippine time throughout."""

from collections import defaultdict
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd
from accounts.validators import age_on

FOLLOW_UP_DAYS = 28  # a follow-up is due this long after the last finalized record (user's call)
LEVEL_FIRST = 3      # NRS-2002 ≥ 3 → at nutritional risk, listed first


def _num(v):
    return float(v) if v is not None else None


def build_ncp_overview(rnd, now=None):
    from scheduling.models import Appointment, RndClientRelationship
    from scheduling.patient_insights import person, ph_tz

    from .models import NcpRecord, PreConsultationScreening

    now = now or timezone.now()
    ph = ph_tz()
    today = now.astimezone(ph).date()
    month_start = today.replace(day=1)

    rels = list(RndClientRelationship.objects.filter(rnd=rnd).select_related("client", "client__client_profile"))
    by_rel = {r.id: r for r in rels}
    records = list(NcpRecord.objects.filter(relationship__in=rels).select_related("appointment").order_by("created_at"))

    # follow-up or initial, worked out in one pass (NcpRecord.is_follow_up() per row would be a query each)
    per_rel = defaultdict(list)
    for rec in records:
        per_rel[rec.relationship_id].append(rec)
    meta = {}
    for rid, recs in per_rel.items():
        finalized_seen, follow_no = False, 0
        for rec in recs:
            follow = finalized_seen
            if follow:
                follow_no += 1
            meta[rec.id] = (follow, follow_no if follow else None)
            if rec.status == NcpRecord.Status.COMPLETED:
                finalized_seen = True

    def patient(rel):
        c = rel.client
        prof = getattr(c, "client_profile", None)
        p = person(c)
        p.update({
            "age": age_on(prof.date_of_birth, today) if prof and prof.date_of_birth else None,
            "sex": prof.sex if prof else None,
        })
        return p

    def missing_for(rec, follow):
        # same list as NcpRecord.finalize_missing(), without its follow-up query
        blank = lambda v: v is None or str(v).strip() == ""  # noqa: E731
        out = []
        if blank(rec.weight_kg) or blank(rec.height_cm):
            out.append("weight and height")
        if blank(rec.pes_problem):
            out.append("PES problem")
        if blank(rec.pes_etiology) or blank(rec.pes_signs):
            out.append("PES etiology and signs")
        if blank(rec.diet_prescription):
            out.append("diet prescription")
        if blank(rec.target_kcal):
            out.append("target kcal")
        if follow and blank(rec.goal_status):
            out.append("goal status")
        return out

    rows = []
    for rec in reversed(records):  # newest first
        rel = by_rel[rec.relationship_id]
        follow, no = meta[rec.id]
        rows.append({
            "id": rec.id, "relationship_id": rel.id, "relationship_status": rel.status, "patient": patient(rel),
            "status": rec.status, "is_follow_up": follow, "follow_up_no": no,
            "encounter_date": rec.encounter_date, "created_at": rec.created_at, "updated_at": rec.updated_at,
            "pes_problem": rec.pes_problem, "target_kcal": _num(rec.target_kcal),
            "goal_status": rec.goal_status, "goal_status_label": rec.get_goal_status_display() if rec.goal_status else None,
            "appointment": {"id": rec.appointment_id, "scheduled_at": rec.appointment.scheduled_at, "type_label": rec.appointment.get_type_display()}
            if rec.appointment_id else None,
            "missing": missing_for(rec, follow) if rec.status == NcpRecord.Status.DRAFT else [],
        })

    # ---------------------------------------------------------------- worklist (active patients only)
    active = [r for r in rels if r.status == RndClientRelationship.Status.ACTIVE]
    screenings = {}
    for s in PreConsultationScreening.objects.filter(client__in=[r.client for r in active]).order_by("-created_at"):
        screenings.setdefault(s.client_id, s)
    linked_appts = {rec.appointment_id for rec in records if rec.appointment_id}
    completed = defaultdict(list)
    for a in Appointment.objects.filter(relationship__in=active, status=Appointment.Status.COMPLETED).order_by("scheduled_at"):
        completed[a.relationship_id].append(a)

    def risk(rel):
        s = screenings.get(rel.client_id)
        return {"nrs_score": s.nrs_score if s else None, "nrs_risk": s.get_nrs_risk_display() if s and s.nrs_risk else None,
                "screening_date": s.created_at if s else None}

    drafts, no_record, follow_due = [], [], []
    for rel in active:
        recs = per_rel.get(rel.id, [])
        draft = next((r for r in recs if r.status == NcpRecord.Status.DRAFT), None)
        finals = [r for r in recs if r.status == NcpRecord.Status.COMPLETED]
        base = {"relationship_id": rel.id, "patient": patient(rel), **risk(rel)}
        if draft:
            follow, no = meta[draft.id]
            drafts.append({**base, "record_id": draft.id, "is_follow_up": follow, "follow_up_no": no,
                           "updated_at": draft.updated_at, "missing": missing_for(draft, follow)})
        elif not finals:
            # An NCP record starts from a consultation, so a newly confirmed
            # patient isn't listed until a consultation is done without one.
            visits = [a for a in completed.get(rel.id, []) if a.id not in linked_appts]
            if visits:
                no_record.append({**base, "visit_date": visits[-1].scheduled_at})
        else:
            last = max(finals, key=lambda r: (r.encounter_date, r.created_at))
            days = (today - last.encounter_date).days
            unrecorded = [a for a in completed.get(rel.id, [])
                          if a.scheduled_at.astimezone(ph).date() > last.encounter_date and a.id not in linked_appts]
            reason = None
            if unrecorded:
                d = unrecorded[-1].scheduled_at.astimezone(ph)
                reason = f"Consultation on {d:%b} {d.day} has no NCP record"
            elif days >= FOLLOW_UP_DAYS:
                reason = f"Last NCP record {days} days ago"
            if reason:
                follow_due.append({**base, "last_record_date": last.encounter_date, "days_since": days, "reason": reason})

    def by_risk(item):
        score = item.get("nrs_score")
        return (0 if score is not None and score >= LEVEL_FIRST else 1, item["patient"]["name"])

    for lst in (no_record, follow_due):
        lst.sort(key=by_risk)
    drafts.sort(key=lambda d: d["updated_at"])  # oldest first — the ones going stale

    prof = getattr(rnd, "rnd_profile", None)
    return {
        "summary": {
            "drafts": len(drafts), "no_record": len(no_record), "follow_up_due": len(follow_due),
            "finalized_this_month": sum(1 for r in records if r.status == NcpRecord.Status.COMPLETED
                                        and r.updated_at.astimezone(ph).date() >= month_start),
        },
        "worklist": {"drafts": drafts, "no_record": no_record, "follow_up_due": follow_due},
        "records": rows,
        "follow_up_days": FOLLOW_UP_DAYS,
        "rnd": {"name": rnd.full_name, "prc_license_number": getattr(prof, "prc_license_number", None),
                "specialization": getattr(prof, "specialization", None)},
    }


class NcpOverviewView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        return Response(build_ncp_overview(request.user))
