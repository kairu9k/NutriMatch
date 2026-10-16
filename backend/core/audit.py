"""Filtering + CSV export for the admin Audit Logs page and the dashboard's
recent activity. Read-only: audit rows are append-only (RA 10173)."""

import csv
import io
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Q

from .models import AuditLog

PH_TZ = ZoneInfo("Asia/Manila")

# Routine rows written by every sign-up / record view — hidden from the
# dashboard's "recent activity" (still on the Audit Logs page).
ROUTINE_ACTIONS = {"consent.given", "client.record_viewed"}


def _ph_day_start(value):
    try:
        d = date.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return datetime.combine(d, time.min, tzinfo=PH_TZ)


def filtered_audit_logs(params):
    """AuditLog queryset for the query params:
    search, action, user (id), date_from / date_to (YYYY-MM-DD, Philippine
    time, inclusive) and scope=admin (actions done by admins or affecting
    accounts/money/settings, without the routine rows)."""
    qs = AuditLog.objects.select_related("user").order_by("-created_at", "-id")

    search = (params.get("search") or "").strip()
    if search:
        q = Q(action__icontains=search) | Q(ip_address__icontains=search) | Q(user__email__icontains=search)
        for part in search.split():
            q |= Q(user__first_name__icontains=part) | Q(user__last_name__icontains=part)
        # plain words from the page's labels ("deactivated", "payout")
        labelled = [code for code, label in AUDIT_LABELS.items() if search.lower() in label.lower()]
        if labelled:
            q |= Q(action__in=labelled)
        qs = qs.filter(q)

    action = params.get("action")
    if action:
        qs = qs.filter(action=action)

    user = params.get("user")
    if user and str(user).isdigit():
        qs = qs.filter(user_id=int(user))

    start = _ph_day_start(params.get("date_from"))
    if start:
        qs = qs.filter(created_at__gte=start)
    end = _ph_day_start(params.get("date_to"))
    if end:
        qs = qs.filter(created_at__lt=end + timedelta(days=1))

    if params.get("scope") == "admin":
        qs = qs.exclude(action__in=ROUTINE_ACTIONS).filter(Q(user__role="admin") | Q(user__isnull=True))
    return qs


CSV_COLUMNS = ["Date (PH time)", "Event", "Action code", "Done by", "Role", "Email", "Target", "Record", "Old values", "New values", "IP address"]


def audit_logs_csv(qs):
    import json

    buf = io.StringIO()
    buf.write("﻿")  # so Excel opens it as UTF-8 (₱, ñ)
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS)
    for log in qs.iterator():
        u = log.user
        writer.writerow([
            log.created_at.astimezone(PH_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            AUDIT_LABELS.get(log.action, log.action),
            log.action,
            u.full_name if u else "System",
            u.role if u else "",
            u.email if u else "",
            log.table_name or "",
            log.record_id if log.record_id is not None else "",
            json.dumps(log.old_values, ensure_ascii=False) if log.old_values else "",
            json.dumps(log.new_values, ensure_ascii=False) if log.new_values else "",
            log.ip_address or "",
        ])
    return buf.getvalue()


# Same wording as frontend/app/utils/admin.js AUDIT_ACTIONS.
AUDIT_LABELS = {
    "consent.given": "Gave data-privacy consent",
    "login.failed": "Failed sign-in",
    "invoice.paid": "Invoice paid",
    "invoice.refunded": "Invoice refunded",
    "payout.released": "Payout released",
    "payout_account.updated": "Payout details updated",
    "rnd.approved": "RND application approved",
    "rnd.rejected": "RND application rejected",
    "setting.updated": "System setting changed",
    "user.deactivated": "Account deactivated",
    "user.reactivated": "Account reactivated",
    "user.password_reset_sent": "Password reset sent",
    "user.removed": "Account removed",
    "client.record_viewed": "Client health record viewed",
    "audit_log.exported": "Audit log exported",
    "appointment.cancelled": "Appointment cancelled by admin",
    "lab_request.created": "Lab tests requested",
    "lab_request.cancelled": "Lab request cancelled",
    "lab_result.uploaded": "Lab result uploaded",
    "lab_result.viewed": "Lab result viewed by RND",
    "lab_result.deleted": "Lab result deleted",
}
