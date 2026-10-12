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
  commission in the period, plus their overall rating.
Printed and exported as CSV from PlatformReports.vue."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

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


def build_report(params, today=None):
    from billing.models import Invoice
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
    gross = sum((i.amount for i in paid), Decimal("0"))
    commission = sum((i.commission_amt or Decimal("0") for i in paid), Decimal("0"))
    refunded = [i for i in paid if i.status == "refunded"]
    refund_pending = [i for i in paid if i.status == "refund_pending"]

    monthly = defaultdict(lambda: {"completed": 0, "cancelled": 0, "payments": 0, "gross": Decimal("0"), "commission": Decimal("0")})
    for a, when in completed:
        monthly[month(when)]["completed"] += 1
    for a, when in cancelled:
        monthly[month(when)]["cancelled"] += 1
    for i in paid:
        m = monthly[month(i.paid_at)]
        m["payments"] += 1
        m["gross"] += i.amount
        m["commission"] += i.commission_amt or Decimal("0")

    by_format = defaultdict(int)
    for a, _ in completed:
        by_format[a.get_type_display()] += 1

    per_rnd = defaultdict(lambda: {"consultations": 0, "payments": 0, "gross": Decimal("0"), "commission": Decimal("0")})
    for a, _ in completed:
        per_rnd[a.relationship.rnd_id]["consultations"] += 1
    for i in paid:
        r = per_rnd[i.relationship.rnd_id]
        r["payments"] += 1
        r["gross"] += i.amount
        r["commission"] += i.commission_amt or Decimal("0")
    ratings = {row["rnd"]: row for row in Review.objects.values("rnd").annotate(avg=Avg("rating"), n=Count("id"))}
    rnds = []
    for p in RndProfile.objects.filter(is_verified=True).select_related("user"):
        s = per_rnd.get(p.user_id, {"consultations": 0, "payments": 0, "gross": Decimal("0"), "commission": Decimal("0")})
        rt = ratings.get(p.user_id)
        rnds.append({
            "id": p.user_id, "name": p.user.full_name, "specialization": p.specialization,
            "consultations": s["consultations"], "payments": s["payments"], "gross": _money(s["gross"]),
            "commission": _money(s["commission"]), "rnd_share": _money(s["gross"] - s["commission"]),
            "rating": round(float(rt["avg"]), 1) if rt and rt["avg"] else None, "reviews": rt["n"] if rt else 0,
        })
    rnds.sort(key=lambda r: (-r["consultations"], -r["gross"], r["name"]))

    return {
        "period": {"key": params.get("period") or ("custom" if params.get("from") else "this_month"), "label": label,
                   "from": start.isoformat(), "to": end.isoformat()},
        "generated_at": timezone.now(),
        "consultations": {"completed": len(completed), "cancelled": len(cancelled), "by_format": dict(by_format)},
        "money": {
            "payments": len(paid), "gross": _money(gross), "commission": _money(commission), "rnd_share": _money(gross - commission),
            "refunded": {"count": len(refunded), "amount": _money(sum((i.amount for i in refunded), Decimal("0")))},
            "refund_pending": {"count": len(refund_pending), "amount": _money(sum((i.amount for i in refund_pending), Decimal("0")))},
        },
        "people": {
            "new_clients": User.objects.filter(role=User.Role.CLIENT, created_at__gte=lo, created_at__lt=hi).count(),
            "rnds_approved": RndProfile.objects.filter(is_verified=True, verified_at__gte=lo, verified_at__lt=hi).count(),
            "support_requests": SupportTicket.objects.filter(created_at__gte=lo, created_at__lt=hi).count(),
        },
        "monthly": [
            {"month": k, "completed": v["completed"], "cancelled": v["cancelled"], "payments": v["payments"],
             "gross": _money(v["gross"]), "commission": _money(v["commission"])}
            for k, v in sorted(monthly.items())
        ],
        "rnds": rnds,
    }


class AdminReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            return Response(build_report(request.query_params))
        except ValueError:
            return Response({"detail": "Use dates like 2026-10-01."}, status=400)
