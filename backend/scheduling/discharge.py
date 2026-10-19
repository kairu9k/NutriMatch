"""Discharging a patient: the RND ends care. The record stays readable to
both sides but can't be changed; booking the RND again reopens it."""

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

from .models import Appointment, RndClientRelationship

MIN_REASON = 10
READ_ONLY_MESSAGE = "This patient was discharged, so their record is read-only."


def ensure_open(relationship):
    """Refuse changes to a discharged patient's record (NCP, progress, meal plans, messages)."""
    if relationship.status == RndClientRelationship.Status.DISCHARGED:
        raise PermissionDenied(READ_ONLY_MESSAGE)


def discharge_blockers(relationship):
    """What has to be dealt with before care can end — empty when it's fine."""
    from clinical.models import NcpRecord

    blockers = []
    open_appts = relationship.appointments.filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED])
    if open_appts.filter(scheduled_at__gt=timezone.now()).exists():
        blockers.append("Cancel their upcoming consultation first.")
    elif open_appts.exists():
        blockers.append("Mark their last consultation as complete first.")
    if NcpRecord.objects.filter(relationship=relationship, status=NcpRecord.Status.DRAFT).exists():
        blockers.append("Finish or delete their NCP draft first.")
    return blockers


def discharge(relationship, by, reason, *, ended_by=RndClientRelationship.EndedBy.RND):
    """End care. `by` is the RND (or the admin); `ended_by` says how it ended:
    the RND discharged them, it ended on its own after the client's request
    (by=None), or NutriMatch ended it (e.g. the RND was deactivated)."""
    from communication.models import Reminder
    from communication.services import notify
    from core.models import AuditLog
    from nutrition.models import MealPlan

    now = timezone.now()
    rnd = relationship.rnd
    with transaction.atomic():
        relationship.status = RndClientRelationship.Status.DISCHARGED
        relationship.ended_at = now
        relationship.discharge_reason = reason
        relationship.ended_by = ended_by
        relationship.discharge_requested_at = None
        relationship.save(update_fields=["status", "ended_at", "discharge_reason", "ended_by",
                                         "discharge_requested_at", "updated_at"])
        archived = MealPlan.objects.filter(relationship=relationship, status=MealPlan.Status.ACTIVE).update(
            status=MealPlan.Status.ARCHIVED)
        stopped = Reminder.objects.filter(relationship=relationship, is_active=True).update(is_active=False)
        AuditLog.objects.create(
            user=by, action="relationship.discharged", table_name="rnd_client_relationships", record_id=relationship.id,
            old_values={"status": "active"},
            new_values={"status": "discharged", "reason": reason[:1000], "ended_by": ended_by,
                        "meal_plans_archived": archived, "reminders_stopped": stopped},
        )
        if ended_by == RndClientRelationship.EndedBy.RND:
            client_text = (f"{rnd.full_name} has completed your care at NutriMatch. Reason: {reason} "
                           "Your records stay available, and you can book them again any time.")
        else:
            client_text = (f"Your care with RND {rnd.full_name} has ended. {reason} "
                           "Your records stay available, and you can book any RND now.")
            notify(recipient=rnd, notifiable_type="relationship", notifiable_id=relationship.id,
                   subject="Patient's care ended",
                   content=f"Your care for {relationship.client.full_name} has ended. {reason} Their record is now read-only.")
        notify(
            recipient=relationship.client,
            notifiable_type="relationship",
            notifiable_id=relationship.id,
            subject="Your care plan has ended",
            content=client_text,
        )

    client = relationship.client

    def _email():
        from accounts.emails import send_notice_email

        try:
            by_rnd = ended_by == RndClientRelationship.EndedBy.RND
            send_notice_email(
                client,
                subject=f"Your care with {rnd.full_name} has ended",
                heading="Your care plan has ended",
                paragraphs=[
                    f"{rnd.full_name} has completed your nutrition care on NutriMatch." if by_rnd
                    else f"Your nutrition care with RND {rnd.full_name} has ended.",
                    "Your past consultations, meal plans and progress stay in your account. "
                    "If you need help again, you can book an RND any time.",
                ],
                highlight=f"Note from your RND: {reason}" if by_rnd else reason,
                button_label="Open NutriMatch",
                button_url=f"{settings.FRONTEND_URL}/client-dashboard",
                preheader=f"Your care with {rnd.full_name} has ended.",
            )
        except Exception:  # best effort — the discharge itself is already saved
            pass

    transaction.on_commit(_email)
    return relationship


class DischargeSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=1000, trim_whitespace=True)

    def validate_reason(self, value):
        if len(value) < MIN_REASON:
            raise serializers.ValidationError(f"Give a reason of at least {MIN_REASON} characters.")
        return value


class RndDischargeView(APIView):
    """GET → can this patient be discharged (and if not, why); POST {reason} → discharge."""

    permission_classes = [IsRnd]

    def _rel(self, request, pk):
        return get_object_or_404(RndClientRelationship.objects.select_related("client"), pk=pk, rnd=request.user)

    def get(self, request, pk):
        rel = self._rel(request, pk)
        blockers = discharge_blockers(rel) if rel.status == RndClientRelationship.Status.ACTIVE else \
            ["Only an active patient can be discharged."]
        return Response({"can_discharge": not blockers, "blockers": blockers})

    def post(self, request, pk):
        rel = self._rel(request, pk)
        if rel.status != RndClientRelationship.Status.ACTIVE:
            raise serializers.ValidationError({"detail": "Only an active patient can be discharged."})
        blockers = discharge_blockers(rel)
        if blockers:
            raise serializers.ValidationError({"detail": " ".join(blockers), "blockers": blockers})
        data = DischargeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        discharge(rel, request.user, data.validated_data["reason"])
        return Response({"id": rel.id, "status": rel.status, "ended_at": rel.ended_at, "discharge_reason": rel.discharge_reason})
