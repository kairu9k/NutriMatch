"""Admin dashboard extras (GET /api/admin/dashboard/), next to platform-stats:

- today: consultations today / next 7 days, unpaid ones starting within 24 h,
  cancelled and completed in the last 7 days;
- attention: things an admin should act on, most urgent first, each with a
  link — booking requests unconfirmed > 24 h, unpaid consultations starting
  soon, support requests waiting, RND applications, refunds to send, RNDs
  with money but no payout details, approved RNDs clients can't book yet,
  new 1–2★ reviews (14 days);
- compare: this month so far vs the same days of last month (consultations
  completed, payments received, commission, new clients), with % change;
- overview: three short columns (2026-10-24, user's plan) for clients, RNDs
  and the platform, each a few figures plus a 6-month trend (PH months)."""

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
        agg = paid.aggregate(g=Sum("amount"))
        # Refunded money earns no commission (same rule as core/reports.py).
        kept = paid.exclude(status__in=["refunded", "refund_pending"]).aggregate(c=Sum("commission_amt"))
        return {
            "consultations": Appointment.objects.filter(status="completed", completed_at__gte=lo, completed_at__lt=hi).count(),
            "payments": float(agg["g"] or Decimal("0")),
            "commission": float(kept["c"] or Decimal("0")),
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
        "The RND hasn't confirmed yet. A nudge may help.", "/admin-appointments")
    support = SupportTicket.objects.filter(status=SupportTicket.Status.OPEN).count()
    add("warning", "support", support, f"{support} support request{'s' if support != 1 else ''} waiting for a reply",
        "Clients and RNDs are told we usually reply within 24 hours.", "/admin-support")
    pending = RndProfile.objects.filter(review_status="pending", user__is_active=True).count()
    add("warning", "applications", pending, f"{pending} RND application{'s' if pending != 1 else ''} to review",
        "Check each PRC license before approving.", "/rnd-verification")
    refunds = Invoice.objects.filter(status="refund_pending").count()
    add("warning", "refunds", refunds, f"{refunds} refund{'s' if refunds != 1 else ''} to send",
        "Refund in PayMongo, then press Mark as refunded.", "/billing-commission?tab=refunds")

    no_details, due = [], []
    for rnd in User.objects.filter(role=User.Role.RND, rnd_profile__is_verified=True, is_active=True):
        e = rnd_earnings(rnd, now)
        if not e["has_payout_account"] and (e["posted"] + e["pending"]) > 0:
            no_details.append({"id": rnd.id, "name": rnd.full_name})
        if e["eligible"]:
            due.append({"id": rnd.id, "name": rnd.full_name, "amount": e["posted"]})
    due_total = sum(d["amount"] for d in due)
    add("warning", "payouts_due", len(due),
        f"₱{due_total:,.0f} in payouts to send to {len(due)} RND{'s' if len(due) != 1 else ''}",
        "Posted balances of at least ₱500 with payout details on file.", "/payouts",
        [{"id": d["id"], "name": d["name"]} for d in due])
    add("info", "payout_details", len(no_details),
        f"{len(no_details)} RND{'s' if len(no_details) != 1 else ''} with money but no payout details",
        "They can't be paid until they add GCash or bank details in Earnings.", "/payouts", no_details)

    bookable = set(bookable_rnd_profiles().values_list("pk", flat=True))
    hidden = [{"id": p.user_id, "name": p.user.full_name} for p in
              RndProfile.objects.filter(is_verified=True, user__is_active=True).select_related("user") if p.pk not in bookable]
    add("info", "not_bookable", len(hidden),
        f"{len(hidden)} approved RND{'s' if len(hidden) != 1 else ''} clients can't book yet",
        "Missing a fee, bio or weekly hours. Their dashboard lists what's left.", "/users?tab=rnds", hidden)

    low = list(Review.objects.filter(rating__lte=2, created_at__gte=now - timedelta(days=LOW_RATING_DAYS)).select_related("rnd"))
    add("info", "low_reviews", len(low), f"{len(low)} new 1–2★ review{'s' if len(low) != 1 else ''}",
        f"From the last {LOW_RATING_DAYS} days. Worth a look.", "/users?tab=rnds",
        [{"id": r.rnd_id, "name": f"{r.rnd.full_name} ({r.rating}★)"} for r in low])

    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(items, key=lambda i: order[i["level"]])


def _month_starts(now, n=6):
    """The first moment of each of the last n PH months, oldest first, plus the
    start of next month as the closing edge."""
    local = now.astimezone(_ph()).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    starts = [local]
    for _ in range(n - 1):
        starts.insert(0, (starts[0] - timedelta(days=1)).replace(day=1))
    nxt = (local + timedelta(days=32)).replace(day=1)
    return starts + [nxt]


def _trend(edges, count):
    """[{month: 'Oct', value}] for each month between consecutive edges."""
    return [{"month": f"{lo:%b}", "value": count(lo, hi)} for lo, hi in zip(edges, edges[1:])]


def _overview(now):
    from billing.models import Invoice
    from profiles.models import RndAvailabilitySchedule, RndProfile
    from profiles.services import bookable_rnd_profiles
    from scheduling.models import Appointment, RndClientRelationship

    edges = _month_starts(now)
    month_start = edges[-2]
    edges[-1] = now  # this month counts up to now, like the figures beside it
    clients = User.objects.filter(role=User.Role.CLIENT, is_active=True)
    total_clients = clients.count()
    onboarded = clients.exclude(onboarding_completed_at__isnull=True).count()

    # RNDs: approved, actually consulting (a completed consultation in 30 days),
    # and how full the bookable ones' next 7 days are (booked hours over their
    # weekly hours; time off isn't subtracted, so it's a slight underestimate).
    approved = RndProfile.objects.filter(is_verified=True, user__is_active=True)
    active_30 = (Appointment.objects.filter(status="completed", completed_at__gte=now - timedelta(days=30))
                 .values("relationship__rnd").distinct().count())
    bookable_users = list(bookable_rnd_profiles().values_list("user_id", flat=True))
    weekly_minutes = 0
    from django.db.models import Q

    from core.ph_time import ph_today

    today, week_end = ph_today(), ph_today() + timedelta(days=6)
    blocks = RndAvailabilitySchedule.objects.filter(
        rnd_id__in=bookable_users, is_available=True, effective_from__lte=week_end,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
    for b in blocks:
        weekly_minutes += max(0, (b.end_time.hour * 60 + b.end_time.minute) - (b.start_time.hour * 60 + b.start_time.minute))
    booked_minutes = sum(
        a.duration_minutes or 60 for a in Appointment.objects.filter(
            relationship__rnd_id__in=bookable_users, status__in=["pending", "confirmed"],
            scheduled_at__gte=now, scheduled_at__lt=now + timedelta(days=7))
    )

    # Platform: of the consultations due in the last 30 days, how many were cancelled.
    due = Appointment.objects.filter(scheduled_at__gte=now - timedelta(days=30), scheduled_at__lt=now,
                                     status__in=["completed", "cancelled"])
    due_n = due.count()
    paid_month = Invoice.objects.filter(paid_at__gte=month_start, paid_at__lt=now).aggregate(g=Sum("amount"))["g"]

    return {
        "clients": {
            "in_care": RndClientRelationship.objects.filter(status="active").values("client").distinct().count(),
            "new_this_month": clients.filter(created_at__gte=month_start).count(),
            "onboarded_pct": round(onboarded / total_clients * 100) if total_clients else None,
            "total": total_clients,
            "trend": _trend(edges, lambda lo, hi: User.objects.filter(role=User.Role.CLIENT, created_at__gte=lo, created_at__lt=hi).count()),
        },
        "rnds": {
            "approved": approved.count(),
            "active_30_days": active_30,
            "bookable": len(bookable_users),
            "calendar_filled_pct": round(booked_minutes / weekly_minutes * 100) if weekly_minutes else None,
            "trend": _trend(edges, lambda lo, hi: Appointment.objects.filter(status="completed", completed_at__gte=lo, completed_at__lt=hi)
                            .values("relationship__rnd").distinct().count()),
        },
        "platform": {
            "consultations_this_month": Appointment.objects.filter(status="completed", completed_at__gte=month_start).count(),
            "payments_this_month": float(paid_month or Decimal("0")),
            "cancelled_pct_30_days": round(due.filter(status="cancelled").count() / due_n * 100) if due_n else None,
            "trend": _trend(edges, lambda lo, hi: float(Invoice.objects.filter(paid_at__gte=lo, paid_at__lt=hi)
                                                         .aggregate(g=Sum("amount"))["g"] or Decimal("0"))),
        },
    }


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
            "overview": _overview(now),
        })
