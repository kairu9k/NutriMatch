"""Platform report for a chosen period (GET /api/admin/reports/?period=…).

period: this_month | last_month | last_3_months | this_year | all (default
this_month), or from=YYYY-MM-DD&to=YYYY-MM-DD. Dates are Philippine dates.

- consultations: completed (by completed_at, else scheduled_at) and
  cancelled (by scheduled_at) in the period, completed by format;
- money: payments received in the period (Invoice.paid_at) — gross, the
  frozen commission and the RNDs' share — and how many of those were
  refunded or are waiting for a refund;
- people: new client accounts, RNDs approved, support requests opened;
- monthly: the same consultation / money figures per month;
- rnds: every approved RND's completed consultations, payments and
  commission in the period, plus their overall rating;
- clients / rnd_stats / reasons / payouts (2026-10-24, Reports tabs):
  sign-ups, onboarding, care, repeat rate and days to a first consultation;
  applications, review time, active RNDs, caseload and ratings; why
  consultations were cancelled; payouts sent and the take rate.
Every month in the period is listed (empty ones too) so charts don't skip.
Printed and exported as CSV from PlatformReports.vue."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from statistics import median

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdmin

PERIODS = {
    "this_month": "This month", "last_month": "Last month", "last_3_months": "Last 3 months",
    "this_year": "This year", "all": "All time",
}


def _ph():
    from scheduling.patient_insights import ph_tz

    return ph_tz()


def period_bounds(params, today=None):
    """(start_date, end_date inclusive, label) in PH dates."""
    today = today or timezone.now().astimezone(_ph()).date()
    if params.get("from") and params.get("to"):
        start, end = date.fromisoformat(params["from"]), date.fromisoformat(params["to"])
        if end < start:
            start, end = end, start
        return start, end, f"{start:%b} {start.day}, {start.year} – {end:%b} {end.day}, {end.year}"
    key = params.get("period") or "this_month"
    first = today.replace(day=1)
    if key == "last_month":
        end = first - timedelta(days=1)
        return end.replace(day=1), end, PERIODS[key]
    if key == "last_3_months":
        m = first.month - 2
        y = first.year + (m - 1) // 12
        return date(y, (m - 1) % 12 + 1, 1), today, PERIODS[key]
    if key == "this_year":
        return date(today.year, 1, 1), today, PERIODS[key]
    if key == "all":
        return date(2000, 1, 1), today, PERIODS[key]
    return first, today, PERIODS["this_month"]


def _aware(d, end=False):
    return datetime.combine(d + timedelta(days=1) if end else d, time.min, tzinfo=_ph())


def _money(v):
    return float((v or Decimal("0")).quantize(Decimal("0.01")))


def _months_between(first, last):
    """'YYYY-MM' for every month from first to last (dates), inclusive."""
    out, y, m = [], first.year, first.month
    while (y, m) <= (last.year, last.month):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _clients(lo, hi, now):
    from scheduling.models import Appointment, RndClientRelationship

    new = User.objects.filter(role=User.Role.CLIENT, created_at__gte=lo, created_at__lt=hi)
    # first completed consultation per client, and how many they had by the period end
    firsts, counts = {}, defaultdict(int)
    for a in (Appointment.objects.filter(status="completed", completed_at__lt=hi)
              .select_related("relationship__client").order_by("completed_at")):
        cid = a.relationship.client_id
        counts[cid] += 1
        firsts.setdefault(cid, a)
    seen_in_period = {a.relationship.client_id for a in Appointment.objects.filter(
        status="completed", completed_at__gte=lo, completed_at__lt=hi).select_related("relationship")}
    waits = [(a.completed_at - a.relationship.client.created_at).days
             for a in firsts.values() if lo <= a.completed_at < hi]
    waiting = (RndClientRelationship.objects.filter(status="pending", appointments__status__in=["pending", "confirmed"],
                                                    appointments__scheduled_at__gte=now)
               .values("client").distinct().count())
    return {
        "new": new.count(),
        "onboarded_of_new": new.exclude(onboarding_completed_at__isnull=True).count(),
        "in_care_now": RndClientRelationship.objects.filter(status="active").values("client").distinct().count(),
        "waiting_now": waiting,
        "discharged": RndClientRelationship.objects.filter(status="discharged", ended_at__gte=lo, ended_at__lt=hi).count(),
        "consulted": len(seen_in_period),
        # of the clients seen in the period, how many have had 2+ consultations in all
        "repeat_pct": round(sum(1 for c in seen_in_period if counts[c] >= 2) / len(seen_in_period) * 100) if seen_in_period else None,
        "days_to_first_median": round(median(waits)) if waits else None,
    }


def _rnd_stats(lo, hi):
    from profiles.models import RndProfile
    from scheduling.models import Appointment, Review, RndClientRelationship

    applied = RndProfile.objects.filter(created_at__gte=lo, created_at__lt=hi, user__email_verified_at__isnull=False)
    reviewed = list(RndProfile.objects.filter(reviewed_at__gte=lo, reviewed_at__lt=hi).exclude(review_status="pending"))
    approved_now = RndProfile.objects.filter(is_verified=True, user__is_active=True)
    approved_n = approved_now.count()
    in_care = RndClientRelationship.objects.filter(status="active").count()
    reviews = Review.objects.filter(created_at__gte=lo, created_at__lt=hi)
    avg = reviews.aggregate(a=Avg("rating"))["a"]
    return {
        "applications": applied.count(),
        "approved": sum(1 for p in reviewed if p.review_status == "approved"),
        "rejected": sum(1 for p in reviewed if p.review_status == "rejected"),
        "days_to_review_median": round(median([(p.reviewed_at - p.created_at).days for p in reviewed])) if reviewed else None,
        "approved_now": approved_n,
        "active": Appointment.objects.filter(status="completed", completed_at__gte=lo, completed_at__lt=hi)
        .values("relationship__rnd").distinct().count(),
        "taking_new_clients": approved_now.filter(available_for_new_clients=True).count(),
        "patients_per_rnd": round(in_care / approved_n, 1) if approved_n else None,
        "rating": round(float(avg), 1) if avg else None,
        "reviews": reviews.count(),
    }


def build_report(params, today=None):
    from billing.models import Invoice, Payout
    from billing.services import NOT_PAID_REASON
    from communication.models import SupportTicket
    from profiles.models import RndProfile
    from scheduling.models import Appointment, Review

    start, end, label = period_bounds(params, today)
    lo, hi = _aware(start), _aware(end, end=True)
    ph = _ph()
    month = lambda dt: dt.astimezone(ph).strftime("%Y-%m")  # noqa: E731

    appts = list(Appointment.objects.filter(status__in=["completed", "cancelled"])
                 .select_related("relationship"))
    completed, cancelled = [], []
    for a in appts:
        when = (a.completed_at or a.scheduled_at) if a.status == "completed" else a.scheduled_at
        if lo <= when < hi:
            (completed if a.status == "completed" else cancelled).append((a, when))

    paid = list(Invoice.objects.filter(paid_at__gte=lo, paid_at__lt=hi).select_related("relationship"))
    payouts = list(Payout.objects.filter(released_at__gte=lo, released_at__lt=hi))
    gross = sum((i.amount for i in paid), Decimal("0"))
    refunded = [i for i in paid if i.status == "refunded"]
    refund_pending = [i for i in paid if i.status == "refund_pending"]
    # Commission and the RNDs' share only come from payments that were kept —
    # money refunded (or waiting for a refund) goes back to the client.
    kept = [i for i in paid if i.status not in ("refunded", "refund_pending")]
    kept_gross = sum((i.amount for i in kept), Decimal("0"))
    commission = sum((i.commission_amt or Decimal("0") for i in kept), Decimal("0"))

    monthly = defaultdict(lambda: {"completed": 0, "cancelled": 0, "payments": 0, "gross": Decimal("0"), "commission": Decimal("0"),
                                   "rnd_share": Decimal("0"), "new_clients": 0, "applications": 0})
    for a, when in completed:
        monthly[month(when)]["completed"] += 1
    for a, when in cancelled:
        monthly[month(when)]["cancelled"] += 1
    for i in paid:
        m = monthly[month(i.paid_at)]
        m["payments"] += 1
        m["gross"] += i.amount
        if i in kept:
            m["commission"] += i.commission_amt or Decimal("0")
            m["rnd_share"] += i.amount - (i.commission_amt or Decimal("0"))
    for u in User.objects.filter(role=User.Role.CLIENT, created_at__gte=lo, created_at__lt=hi).only("created_at"):
        monthly[month(u.created_at)]["new_clients"] += 1
    for prof in RndProfile.objects.filter(created_at__gte=lo, created_at__lt=hi, user__email_verified_at__isnull=False).only("created_at"):
        monthly[month(prof.created_at)]["applications"] += 1
    # every month in the period, from the first with any activity ("all time"
    # starts in 2000), so a chart shows quiet months as zero instead of skipping them
    first_month = min(monthly) if monthly else f"{end:%Y-%m}"
    span_start = max(start, date.fromisoformat(f"{first_month}-01")) if params.get("period") == "all" else start
    month_keys = _months_between(span_start, end)

    reasons = {"no_show": 0, "not_paid": 0, "other": 0}
    for a, _ in cancelled:
        why = a.cancellation_reason or ""
        reasons["no_show" if why.startswith("No-show") else "not_paid" if why == NOT_PAID_REASON else "other"] += 1

    by_format = defaultdict(int)
    for a, _ in completed:
        by_format[a.get_type_display()] += 1

    per_rnd = defaultdict(lambda: {"consultations": 0, "payments": 0, "gross": Decimal("0"), "kept": Decimal("0"), "commission": Decimal("0")})
    for a, _ in completed:
        per_rnd[a.relationship.rnd_id]["consultations"] += 1
    for i in paid:
        r = per_rnd[i.relationship.rnd_id]
        r["payments"] += 1
        r["gross"] += i.amount
        if i in kept:
            r["kept"] += i.amount
            r["commission"] += i.commission_amt or Decimal("0")
    ratings = {row["rnd"]: row for row in Review.objects.values("rnd").annotate(avg=Avg("rating"), n=Count("id"))}
    rnds = []
    for p in RndProfile.objects.filter(is_verified=True).select_related("user"):
        s = per_rnd.get(p.user_id, {"consultations": 0, "payments": 0, "gross": Decimal("0"), "kept": Decimal("0"), "commission": Decimal("0")})
        rt = ratings.get(p.user_id)
        rnds.append({
            "id": p.user_id, "name": p.user.full_name, "specialization": p.specialization,
            "consultations": s["consultations"], "payments": s["payments"], "gross": _money(s["gross"]),
            "commission": _money(s["commission"]), "rnd_share": _money(s["kept"] - s["commission"]),
            "rating": round(float(rt["avg"]), 1) if rt and rt["avg"] else None, "reviews": rt["n"] if rt else 0,
        })
    rnds.sort(key=lambda r: (-r["consultations"], -r["gross"], r["name"]))

    return {
        "period": {"key": params.get("period") or ("custom" if params.get("from") else "this_month"), "label": label,
                   "from": start.isoformat(), "to": end.isoformat()},
        "generated_at": timezone.now(),
        "consultations": {"completed": len(completed), "cancelled": len(cancelled), "by_format": dict(by_format),
                          "cancelled_reasons": reasons},
        "money": {
            "payments": len(paid), "gross": _money(gross), "commission": _money(commission), "rnd_share": _money(kept_gross - commission),
            "take_rate_pct": round(float(commission / kept_gross * 100), 1) if kept_gross else None,
            "payouts_sent": {"count": len(payouts), "amount": _money(sum((x.amount for x in payouts), Decimal("0")))},
            "refunded": {"count": len(refunded), "amount": _money(sum((i.amount for i in refunded), Decimal("0")))},
            "refund_pending": {"count": len(refund_pending), "amount": _money(sum((i.amount for i in refund_pending), Decimal("0")))},
        },
        "people": {
            "new_clients": User.objects.filter(role=User.Role.CLIENT, created_at__gte=lo, created_at__lt=hi).count(),
            "rnds_approved": RndProfile.objects.filter(is_verified=True, verified_at__gte=lo, verified_at__lt=hi).count(),
            "support_requests": SupportTicket.objects.filter(created_at__gte=lo, created_at__lt=hi).count(),
        },
        "monthly": [
            {"month": k, "completed": monthly[k]["completed"], "cancelled": monthly[k]["cancelled"], "payments": monthly[k]["payments"],
             "gross": _money(monthly[k]["gross"]), "commission": _money(monthly[k]["commission"]),
             "rnd_share": _money(monthly[k]["rnd_share"]), "new_clients": monthly[k]["new_clients"], "applications": monthly[k]["applications"]}
            for k in month_keys
        ],
        "clients": _clients(lo, hi, timezone.now()),
        "rnd_stats": _rnd_stats(lo, hi),
        "rnds": rnds,
    }


class AdminReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            return Response(build_report(request.query_params))
        except ValueError:
            return Response({"detail": "Use dates like 2026-10-01."}, status=400)
