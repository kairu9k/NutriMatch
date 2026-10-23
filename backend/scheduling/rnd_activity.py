"""The RND's own activity (Profile Settings -> History, 2026-10-19, user's
call — like the client's "Your Activity"): consultations, NCP records, meal
plans sent, patients started/ended, reviews received and payouts, newest
first. Built from the real records; nothing is stored for it.

GET /api/rnd/activity/  ->  [{key, type, at, title, detail, link}]
type: consultation | ncp | meal_plan | patient | review | payout
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd
from billing.models import payout_destination

PER_SOURCE = 150  # newest of each kind — plenty for a history page
LIMIT = 400


def _when(dt):
    from .views import format_ph_datetime

    return format_ph_datetime(dt) if dt else ""


def build_activity(rnd):
    from billing.models import Payout
    from clinical.models import NcpRecord
    from nutrition.models import MealPlan

    from .models import Appointment, Review, RndClientRelationship

    items = []

    for a in (Appointment.objects.filter(relationship__rnd=rnd).select_related("relationship__client")
              .order_by("-updated_at")[:PER_SOURCE]):
        name = a.relationship.client.full_name
        kind = a.get_type_display()
        if a.status == Appointment.Status.COMPLETED:
            title, at = f"Completed a {kind.lower()} consultation with {name}", a.completed_at or a.updated_at
        elif a.status == Appointment.Status.CANCELLED:
            title, at = f"{kind} consultation with {name} cancelled", a.updated_at
        elif a.status == Appointment.Status.CONFIRMED:
            title, at = f"Confirmed a {kind.lower()} consultation with {name}", a.updated_at
        else:
            title, at = f"{name} requested a {kind.lower()} consultation", a.created_at
        detail = f"Scheduled {_when(a.scheduled_at)}"
        if a.status == Appointment.Status.CANCELLED and a.cancellation_reason:
            detail += f" · {a.cancellation_reason}"
        items.append({"key": f"a{a.id}", "type": "consultation", "at": at, "title": title, "detail": detail,
                      "link": f"/client-detail/{a.relationship_id}?tab=appointments"})

    for n in (NcpRecord.objects.filter(relationship__rnd=rnd).select_related("relationship__client")
              .order_by("-updated_at")[:PER_SOURCE]):
        name = n.relationship.client.full_name
        done = n.status == NcpRecord.Status.COMPLETED
        items.append({
            "key": f"n{n.id}", "type": "ncp", "at": n.updated_at if done else n.created_at,
            "title": f"{'Finalized' if done else 'Started'} an NCP record for {name}",
            "detail": f"Encounter {n.encounter_date:%b} {n.encounter_date.day}, {n.encounter_date.year}"
                      + (f" · {n.pes_problem}" if n.pes_problem else "") + ("" if done else " · draft"),
            "link": f"/client-detail/{n.relationship_id}?tab=ncp",
        })

    for p in (MealPlan.objects.filter(relationship__rnd=rnd, first_sent_at__isnull=False)
              .select_related("relationship__client").order_by("-sent_at")[:PER_SOURCE]):
        name = p.relationship.client.full_name
        resent = p.sent_at and p.first_sent_at and p.sent_at > p.first_sent_at
        items.append({
            "key": f"p{p.id}", "type": "meal_plan", "at": p.sent_at or p.first_sent_at,
            "title": f"{'Updated and re-sent' if resent else 'Sent'} the meal plan “{p.name}” to {name}",
            "detail": (f"{int(p.target_kcal):,} kcal/day · " if p.target_kcal else "") + p.get_status_display(),
            "link": f"/client-detail/{p.relationship_id}?tab=meal",
        })

    for r in (RndClientRelationship.objects.filter(rnd=rnd).select_related("client")
              .order_by("-updated_at")[:PER_SOURCE]):
        name = r.client.full_name
        if r.started_at:
            items.append({"key": f"rs{r.id}", "type": "patient", "at": r.started_at,
                          "title": f"{name} became your patient", "detail": "Care started when you confirmed their booking",
                          "link": f"/client-detail/{r.id}"})
        if r.status == RndClientRelationship.Status.DISCHARGED and r.ended_at:
            how = {"auto": "Ended automatically (their request)", "admin": "Ended by NutriMatch"}.get(r.ended_by, "Discharged by you")
            items.append({"key": f"re{r.id}", "type": "patient", "at": r.ended_at,
                          "title": f"{name}'s care ended", "detail": how + (f" · {r.discharge_reason}" if r.discharge_reason else ""),
                          "link": f"/client-detail/{r.id}"})
        if r.discharge_requested_at and r.status == RndClientRelationship.Status.ACTIVE:
            items.append({"key": f"rq{r.id}", "type": "patient", "at": r.discharge_requested_at,
                          "title": f"{name} asked to end their care",
                          "detail": r.get_discharge_request_reason_display() if r.discharge_request_reason else "",
                          "link": f"/client-detail/{r.id}"})

    for v in Review.objects.filter(rnd=rnd).select_related("client").order_by("-created_at")[:PER_SOURCE]:
        items.append({"key": f"v{v.id}", "type": "review", "at": v.created_at,
                      "title": f"{v.client.full_name} left a {v.rating}-star review",
                      "detail": f"“{v.comment[:140]}”" if v.comment else "", "link": "/reviews"})

    for pay in Payout.objects.filter(rnd=rnd).order_by("-released_at")[:PER_SOURCE]:
        items.append({"key": f"y{pay.id}", "type": "payout", "at": pay.released_at,
                      "title": f"Payout of ₱{pay.amount:,.2f} sent to your {payout_destination(pay.method, pay.bank_name)}",
                      "detail": f"Reference {pay.reference}", "link": "/earnings"})

    items = [i for i in items if i["at"]]
    items.sort(key=lambda i: i["at"], reverse=True)
    return items[:LIMIT]


class RndActivityView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        return Response(build_activity(request.user))
