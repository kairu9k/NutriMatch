"""Help & Support: clients and RNDs write to the NutriMatch admins from the
floating help button (SupportWidget.vue); admins answer on the Support page.
Message-and-reply, not live chat — admins aren't always online.

User (client/RND):
  GET/POST /api/support/tickets/                 list / open a request
  GET      /api/support/tickets/<id>/            thread (marks admin replies read)
  POST     /api/support/tickets/<id>/messages/   reply (reopens a closed request)
  POST     /api/support/tickets/<id>/close/
  GET      /api/support/links/                   their appointments + invoices to attach
  GET      /api/support/unread/                  {count} for the button's dot
Admin:
  GET  /api/admin/support/tickets/?status=open|answered|closed|all
  GET  /api/admin/support/tickets/<id>/
  POST /api/admin/support/tickets/<id>/messages/  reply → Answered, user notified + emailed
  POST /api/admin/support/tickets/<id>/close/  ·  /reopen/

Each new request and each user reply notifies every active admin in-app and
emails the support inbox (core.support.support_email); each admin reply
notifies and emails the user. Emails are best effort, after commit."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdmin

from .models import SupportMessage, SupportTicket
from .services import notify

logger = logging.getLogger(__name__)

MAX_NEW_PER_HOUR = 5
MAX_OPEN = 10
SUPPORT_NAME = "NutriMatch Support"


class IsClientOrRnd(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.role in (User.Role.CLIENT, User.Role.RND))


def _party_q(user, prefix=""):
    return Q(**{f"{prefix}relationship__client": user}) | Q(**{f"{prefix}relationship__rnd": user})


def _ph(dt):
    from scheduling.views import format_ph_datetime

    return format_ph_datetime(dt)


def _appointment_summary(appt, viewer):
    if appt is None:
        return None
    rel = appt.relationship
    if viewer.role == User.Role.ADMIN:
        with_ = f"{rel.client.full_name} with {rel.rnd.full_name}"
    else:
        other = rel.rnd if rel.client_id == viewer.id else rel.client
        with_ = other.full_name
    return {"id": appt.id, "label": f"{_ph(appt.scheduled_at)} · {appt.get_type_display()} · {with_}", "status": appt.status}


def _invoice_summary(inv):
    if inv is None:
        return None
    return {"id": inv.id, "label": f"INV-{inv.id:04d} · ₱{inv.amount:,.2f} · {inv.get_status_display()}", "status": inv.status}


# ---- serializers -------------------------------------------------------------

class SupportTicketCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=SupportTicket.Category.choices)
    subject = serializers.CharField(min_length=5, max_length=150)
    message = serializers.CharField(min_length=10, max_length=3000)
    appointment = serializers.IntegerField(required=False, allow_null=True)
    invoice = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        from billing.models import Invoice
        from scheduling.models import Appointment

        user = self.context["request"].user
        attrs["subject"] = " ".join(attrs["subject"].split())
        attrs["message"] = attrs["message"].strip()
        if attrs.get("appointment"):
            attrs["appointment"] = Appointment.objects.filter(_party_q(user), pk=attrs["appointment"]).first()
            if attrs["appointment"] is None:
                raise serializers.ValidationError({"appointment": "Pick one of your own appointments."})
        if attrs.get("invoice"):
            attrs["invoice"] = Invoice.objects.filter(_party_q(user), pk=attrs["invoice"]).first()
            if attrs["invoice"] is None:
                raise serializers.ValidationError({"invoice": "Pick one of your own invoices."})
        recent = SupportTicket.objects.filter(user=user, created_at__gte=timezone.now() - timedelta(hours=1)).count()
        if recent >= MAX_NEW_PER_HOUR:
            raise serializers.ValidationError({"detail": "You've sent several requests in the last hour. Please wait for a reply, or add to an existing request."})
        if SupportTicket.objects.filter(user=user).exclude(status=SupportTicket.Status.CLOSED).count() >= MAX_OPEN:
            raise serializers.ValidationError({"detail": f"You have {MAX_OPEN} open requests. Close one you no longer need first."})
        return attrs


class ReplySerializer(serializers.Serializer):
    body = serializers.CharField(min_length=2, max_length=3000)

    def validate_body(self, value):
        return value.strip()


def ticket_summary(t, viewer):
    last = t.messages.order_by("-created_at").first()
    data = {
        "id": t.id, "reference": f"SR-{t.id:04d}", "category": t.category, "category_label": t.get_category_display(),
        "subject": t.subject, "status": t.status, "status_label": t.get_status_display(),
        "last_activity_at": t.last_activity_at, "created_at": t.created_at, "closed_at": t.closed_at,
        "last_message": {"body": last.body[:140], "from_support": last.is_admin} if last else None,
    }
    if viewer.role == User.Role.ADMIN:
        data["unread"] = t.admin_unread
        data["user"] = {"id": t.user_id, "name": t.user.full_name, "email": t.user.email, "role": t.user.role,
                        "profile_photo": t.user.profile_photo}
    else:
        data["unread"] = t.user_unread
    return data


def ticket_detail(t, viewer):
    data = ticket_summary(t, viewer)
    data["appointment"] = _appointment_summary(t.appointment, viewer)
    data["invoice"] = _invoice_summary(t.invoice)
    data["messages"] = [{
        "id": m.id, "body": m.body, "from_support": m.is_admin, "created_at": m.created_at,
        "sender_name": (m.sender.full_name if viewer.role == User.Role.ADMIN and m.sender else SUPPORT_NAME) if m.is_admin
        else (m.sender.full_name if m.sender else t.user.full_name),
    } for m in t.messages.select_related("sender")]
    return data


# ---- notifications -----------------------------------------------------------

def _notify_admins(ticket, subject, content):
    for admin in User.objects.filter(role=User.Role.ADMIN, is_active=True):
        notify(recipient=admin, notifiable_type="support", notifiable_id=ticket.id, subject=subject, content=content)

    def send():
        from accounts.emails import send_branded_email
        from core.support import support_email

        try:
            link = f"{settings.FRONTEND_URL}/admin-support?ticket={ticket.id}"
            send_branded_email(
                to=support_email(), subject=f"[SR-{ticket.id:04d}] {subject}", template="emails/notice.html",
                context={"first_name": "NutriMatch team", "heading": subject, "paragraphs": [content],
                         "highlight": f"{ticket.user.full_name} ({ticket.user.get_role_display()}) · {ticket.get_category_display()}",
                         "button_label": "Open in NutriMatch", "button_url": link},
                text=f"{subject}\n\n{content}\n\n{link}",
            )
        except Exception:  # noqa: BLE001 — best effort, never breaks the request
            logger.exception("Support inbox email failed for ticket %s", ticket.id)

    transaction.on_commit(send)


def _notify_user(ticket, reply):
    notify(recipient=ticket.user, notifiable_type="support", notifiable_id=ticket.id,
           subject="NutriMatch Support replied",
           content=f"Re: {ticket.subject} (SR-{ticket.id:04d}) — {reply.body[:160]}")

    def send():
        from accounts.emails import send_notice_email

        try:
            send_notice_email(
                ticket.user, subject=f"Re: {ticket.subject} [SR-{ticket.id:04d}]", heading="We replied to your request",
                paragraphs=[reply.body, "You can reply from the help button (bottom right) in NutriMatch."],
                highlight=f"Request SR-{ticket.id:04d} · {ticket.subject}",
                button_label="Open my request",
                button_url=f"{settings.FRONTEND_URL}/{'rnd-dashboard' if ticket.user.role == 'rnd' else 'client-dashboard'}?support={ticket.id}",
            )
        except Exception:  # noqa: BLE001
            logger.exception("Support reply email failed for ticket %s", ticket.id)

    transaction.on_commit(send)


# ---- user views --------------------------------------------------------------

def _own_ticket(request, pk):
    return get_object_or_404(SupportTicket.objects.select_related("user", "appointment__relationship__rnd",
                                                                  "appointment__relationship__client", "invoice"),
                             pk=pk, user=request.user)


class SupportTicketListCreateView(APIView):
    permission_classes = [IsClientOrRnd]

    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user).select_related("user")
        return Response([ticket_summary(t, request.user) for t in tickets])

    def post(self, request):
        s = SupportTicketCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with transaction.atomic():
            t = SupportTicket.objects.create(user=request.user, category=d["category"], subject=d["subject"],
                                             appointment=d.get("appointment"), invoice=d.get("invoice"))
            SupportMessage.objects.create(ticket=t, sender=request.user, body=d["message"])
            _notify_admins(t, f"New support request: {t.subject}",
                           f"{request.user.full_name} ({request.user.get_role_display()}) wrote: {d['message'][:300]}")
        return Response(ticket_detail(t, request.user), status=status.HTTP_201_CREATED)


class SupportTicketDetailView(APIView):
    permission_classes = [IsClientOrRnd]

    def get(self, request, pk):
        t = _own_ticket(request, pk)
        if t.user_unread:
            t.user_unread = False
            t.save(update_fields=["user_unread"])
        return Response(ticket_detail(t, request.user))


class SupportTicketReplyView(APIView):
    permission_classes = [IsClientOrRnd]

    def post(self, request, pk):
        t = _own_ticket(request, pk)
        s = ReplySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        with transaction.atomic():
            msg = SupportMessage.objects.create(ticket=t, sender=request.user, body=s.validated_data["body"])
            reopened = t.status == SupportTicket.Status.CLOSED
            t.status = SupportTicket.Status.OPEN
            t.admin_unread = True
            t.closed_at = None
            t.last_activity_at = msg.created_at
            t.save(update_fields=["status", "admin_unread", "closed_at", "last_activity_at"])
            _notify_admins(t, f"{'Reopened' if reopened else 'New reply'}: {t.subject}",
                           f"{request.user.full_name} wrote: {msg.body[:300]}")
        return Response(ticket_detail(t, request.user), status=status.HTTP_201_CREATED)


class SupportTicketCloseView(APIView):
    permission_classes = [IsClientOrRnd]

    def post(self, request, pk):
        t = _own_ticket(request, pk)
        _close(t)
        return Response(ticket_detail(t, request.user))


class SupportLinksView(APIView):
    """The user's recent appointments and invoices to attach to a request."""

    permission_classes = [IsClientOrRnd]

    def get(self, request):
        from billing.models import Invoice
        from scheduling.models import Appointment

        appts = (Appointment.objects.filter(_party_q(request.user))
                 .select_related("relationship__client", "relationship__rnd").order_by("-scheduled_at")[:15])
        invoices = Invoice.objects.filter(_party_q(request.user)).order_by("-created_at")[:15]
        return Response({
            "appointments": [_appointment_summary(a, request.user) for a in appts],
            "invoices": [_invoice_summary(i) for i in invoices],
        })


class SupportUnreadView(APIView):
    permission_classes = [IsClientOrRnd]

    def get(self, request):
        return Response({"count": SupportTicket.objects.filter(user=request.user, user_unread=True).count()})


def _close(t):
    if t.status != SupportTicket.Status.CLOSED:
        t.status = SupportTicket.Status.CLOSED
        t.closed_at = timezone.now()
        t.save(update_fields=["status", "closed_at"])


# ---- admin views -------------------------------------------------------------

def _admin_ticket(pk):
    return get_object_or_404(SupportTicket.objects.select_related("user", "appointment__relationship__rnd",
                                                                  "appointment__relationship__client", "invoice"), pk=pk)


class AdminSupportTicketListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = SupportTicket.objects.select_related("user")
        counts = {s: qs.filter(status=s).count() for s in SupportTicket.Status.values}
        counts["unread"] = qs.filter(admin_unread=True).exclude(status=SupportTicket.Status.CLOSED).count()
        wanted = request.query_params.get("status", "open")
        if wanted in SupportTicket.Status.values:
            qs = qs.filter(status=wanted)
        search = (request.query_params.get("search") or "").strip()
        if search:
            ref = search.upper().removeprefix("SR-").lstrip("0")
            q = Q(subject__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | Q(user__email__icontains=search)
            if ref.isdigit():
                q |= Q(pk=int(ref))
            qs = qs.filter(q)
        return Response({"counts": counts, "results": [ticket_summary(t, request.user) for t in qs[:200]]})


class AdminSupportTicketDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        t = _admin_ticket(pk)
        if t.admin_unread:
            t.admin_unread = False
            t.save(update_fields=["admin_unread"])
        return Response(ticket_detail(t, request.user))


class AdminSupportReplyView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        t = _admin_ticket(pk)
        s = ReplySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        with transaction.atomic():
            msg = SupportMessage.objects.create(ticket=t, sender=request.user, is_admin=True, body=s.validated_data["body"])
            t.status = SupportTicket.Status.ANSWERED
            t.user_unread = True
            t.admin_unread = False
            t.closed_at = None
            t.last_activity_at = msg.created_at
            t.save(update_fields=["status", "user_unread", "admin_unread", "closed_at", "last_activity_at"])
            _notify_user(t, msg)
        return Response(ticket_detail(t, request.user), status=status.HTTP_201_CREATED)


class AdminSupportCloseView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        t = _admin_ticket(pk)
        _close(t)
        return Response(ticket_detail(t, request.user))


class AdminSupportReopenView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        t = _admin_ticket(pk)
        if t.status == SupportTicket.Status.CLOSED:
            t.status = SupportTicket.Status.OPEN
            t.closed_at = None
            t.save(update_fields=["status", "closed_at"])
        return Response(ticket_detail(t, request.user))
