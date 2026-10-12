"""Admin dashboard extras (GET /api/admin/dashboard/), next to platform-stats:

- today: consultations today / next 7 days, unpaid ones starting within 24 h,
  cancelled and completed in the last 7 days;
- attention: things an admin should act on, most urgent first, each with a
  link — booking requests unconfirmed > 24 h, unpaid consultations starting
  soon, support requests waiting, RND applications, refunds to send, RNDs
  with money but no payout details, approved RNDs clients can't book yet,
  new 1–2★ reviews (14 days);
- compare: this month so far vs the same days of last month (consultations
  completed, payments received, commission, new clients), with % change."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdmin

LOW_RATING_DAYS = 14


def _ph():
    from scheduling.patient_insights import ph_tz

    return ph_tz()


def _pct(now_v, before_v):
    now_v, before_v = float(now_v or 0), float(before_v or 0)
    if not before_v:
        return None
    return round((now_v - before_v) / before_v * 100)


def _compare(now):
    from billing.models import Invoice
    from scheduling.models import Appointment

    local = now.astimezone(_ph())
    this_start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_end_day = this_start - timedelta(days=1)
    prev_start = prev_end_day.replace(day=1)
    # Same number of days into last month (capped at its length), so a
    # half-finished month isn't compared with a whole one.
    elapsed = now - this_start
    prev_cut = min(prev_start + elapsed, this_start)

    def figures(lo, hi):
        paid = Invoice.objects.filter(paid_at__gte=lo, paid_at__lt=hi)
        agg = paid.aggregate(g=Sum("amount"), c=Sum("commission_amt"))
        return {
            "consultations": Appointment.objects.filter(status="completed", completed_at__gte=lo, completed_at__lt=hi).count(),
            "payments": float(agg["g"] or Decimal("0")),
            "commission": float(agg["c"] or Decimal("0")),
            "new_clients": User.objects.filter(role=User.Role.CLIENT, created_at__gte=lo, created_at__lt=hi).count(),
        }

    cur, prev = figures(this_start, now), figures(prev_start, prev_cut)
    return {
        "label": f"{this_start:%B} 1–{local.day} vs {prev_start:%B} 1–{(prev_cut - timedelta(seconds=1)).astimezone(_ph()).day}",
        "metrics": [{"key": k, "now": cur[k], "before": prev[k], "change_pct": _pct(cur[k], prev[k])} for k in cur],
    }


def _attention(now, summary):
    from billing.models import Invoice
    from billing.payouts import rnd_earnings
    from communication.models import SupportTicket
    from profiles.models import RndProfile
    from profiles.services import bookable_rnd_profiles
    from scheduling.models import Review

    items = []

    def add(level, key, count, title, detail, link, people=None):
        if count:
            items.append({"level": level, "key": key, "count": count, "title": title, "detail": detail,
                          "link": link, "people": people or []})

    add("critical", "unpaid_soon", summary["unpaid_soon"],
        f"{summary['unpaid_soon']} unpaid consultation{'s' if summary['unpaid_soon'] != 1 else ''} starting within 24 h",
        "They're cancelled automatically at the start time if still unpaid.", "/admin-appointments")
    add("warning", "stale_requests", summary["stale_requests"],
        f"{summary['stale_requests']} booking request{'s' if summary['stale_requests'] != 1 else ''} waiting over {summary['stale_request_hours']} h",
        "The RND hasn't confirmed yet — a nudge may help.", "/admin-appointments")
    support = SupportTicket.objects.filter(status=SupportTicket.Status.OPEN).count()
    add("warning", "support", support, f"{support} support request{'s' if support != 1 else ''} waiting for a reply",
        "Clients and RNDs are told we usually reply within 24 hours.", "/admin-support")
    pending = RndProfile.objects.filter(review_status="pending", user__is_active=True).count()
    add("warning", "applications", pending, f"{pending} RND application{'s' if pending != 1 else ''} to review",
        "Check each PRC license before approving.", "/rnd-verification")
    refunds = Invoice.objects.filter(status="refund_pending").count()
    add("warning", "refunds", refunds, f"{refunds} refund{'s' if refunds != 1 else ''} to send",
        "Refund in PayMongo, then press Mark as refunded.", "/billing-commission?tab=refunds")

    no_details = []
    for rnd in User.objects.filter(role=User.Role.RND, rnd_profile__is_verified=True, is_active=True):
        e = rnd_earnings(rnd, now)
        if not e["has_payout_account"] and (e["posted"] + e["pending"]) > 0:
            no_details.append({"id": rnd.id, "name": rnd.full_name})
    add("info", "payout_details", len(no_details),
        f"{len(no_details)} RND{'s' if len(no_details) != 1 else ''} with money but no payout details",
        "They can't be paid until they add GCash or bank details in Earnings.", "/payouts", no_details)

    bookable = set(bookable_rnd_profiles().values_list("pk", flat=True))
    hidden = [{"id": p.user_id, "name": p.user.full_name} for p in
              RndProfile.objects.filter(is_verified=True, user__is_active=True).select_related("user") if p.pk not in bookable]
    add("info", "not_bookable", len(hidden),
        f"{len(hidden)} approved RND{'s' if len(hidden) != 1 else ''} clients can't book yet",
        "Missing a fee, bio or weekly hours — their dashboard lists what's left.", "/users?tab=rnds", hidden)

    low = list(Review.objects.filter(rating__lte=2, created_at__gte=now - timedelta(days=LOW_RATING_DAYS)).select_related("rnd"))
    add("info", "low_reviews", len(low), f"{len(low)} new 1–2★ review{'s' if len(low) != 1 else ''}",
        f"From the last {LOW_RATING_DAYS} days — worth a look.", "/users?tab=rnds",
        [{"id": r.rnd_id, "name": f"{r.rnd.full_name} · {r.rating}★"} for r in low])

    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(items, key=lambda i: order[i["level"]])


class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from scheduling.admin_views import appointment_summary

        now = timezone.now()
        s = appointment_summary(now)
        return Response({
            "today": {k: s[k] for k in ("today", "next_7_days", "unpaid_soon", "cancelled_7_days", "completed_7_days", "requests")},
            "attention": _attention(now, s),
            "compare": _compare(now),
        })
