"""RND time off: blocking whole days or part of a day on specific dates
(Profile Settings → Availability → Block time off).

GET  /api/rnd/time-off/           upcoming and current blocks
POST /api/rnd/time-off/           {start_date, end_date?, start_time?, end_time?, reason?}
DELETE /api/rnd/time-off/<id>/

Booking already refuses anything that overlaps a block (scheduling
serializers) and Next available skips them (profiles/public.py). Existing
bookings inside a new block are NOT cancelled — POST returns them as
`conflicts` so the RND can cancel or reschedule."""

from datetime import datetime, time, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRnd

from .models import RndTimeOff

MAX_BLOCK_DAYS = 90


def _ph():
    from zoneinfo import ZoneInfo

    return ZoneInfo("Asia/Manila")


class RndTimeOffSerializer(serializers.ModelSerializer):
    whole_day = serializers.BooleanField(read_only=True)

    class Meta:
        model = RndTimeOff
        fields = ["id", "start_date", "end_date", "start_time", "end_time", "whole_day", "reason", "created_at"]
        read_only_fields = ["id", "whole_day", "created_at"]
        extra_kwargs = {
            "end_date": {"required": False},
            "reason": {"required": False, "allow_blank": True, "max_length": 200},
        }

    def validate(self, attrs):
        start, end = attrs["start_date"], attrs.get("end_date") or attrs["start_date"]
        attrs["end_date"] = end
        today = timezone.now().astimezone(_ph()).date()
        if start < today:
            raise serializers.ValidationError({"start_date": ["Pick today or a later date."]})
        if end < start:
            raise serializers.ValidationError({"end_date": ["The end date can't be before the start date."]})
        if (end - start).days + 1 > MAX_BLOCK_DAYS:
            raise serializers.ValidationError({"end_date": [f"Block at most {MAX_BLOCK_DAYS} days at a time."]})
        t1, t2 = attrs.get("start_time"), attrs.get("end_time")
        if (t1 is None) != (t2 is None):
            raise serializers.ValidationError({"end_time": ["Give both a start and an end time, or block the whole day."]})
        if t1 is not None:
            if t2 <= t1:
                raise serializers.ValidationError({"end_time": ["The end time must be after the start time."]})
            if (datetime.combine(start, t2) - datetime.combine(start, t1)) < timedelta(hours=1):
                raise serializers.ValidationError({"end_time": ["Block at least 1 hour."]})
        rnd = self.context.get("rnd")
        if rnd is not None:
            problem = outside_working_hours(rnd.id, start, end, t1, t2)
            if problem:
                raise serializers.ValidationError({"non_field_errors": [problem]})
        return attrs


DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _clock(t):
    return t.strftime("%I:%M %p").lstrip("0")


def outside_working_hours(rnd_id, start, end, t1=None, t2=None):
    """Why a block can't be saved, or None. A block must cover some of the
    RND's weekly hours on at least one of its dates — a whole day needs a
    working day, a part-day block must overlap that day's hours (partly is
    fine: blocking 8–10 AM still blocks 9–10). A range like a week of leave
    only needs one working day in it. Mirrored in Availability.vue."""
    from .models import RndAvailabilitySchedule

    schedules = list(RndAvailabilitySchedule.objects.filter(rnd_id=rnd_id, is_available=True))
    if not schedules:
        return "Add your weekly availability first — there are no hours to block yet."

    def hours_on(day):
        dow = (day.weekday() + 1) % 7  # Python Monday=0 -> model Sunday=0
        return sorted(
            (b for b in schedules
             if b.day_of_week == dow and (not b.effective_from or b.effective_from <= day)
             and (not b.effective_to or b.effective_to >= day)),
            key=lambda b: b.start_time,
        )

    day = start
    while day <= end:
        blocks = hours_on(day)
        if blocks and (t1 is None or any(b.start_time < t2 and b.end_time > t1 for b in blocks)):
            return None
        day += timedelta(days=1)

    if start == end:
        blocks = hours_on(start)
        name = DAY_NAMES[(start.weekday() + 1) % 7]
        if not blocks:
            return f"You have no hours on {name}s, so there's nothing to block."
        hours = ", ".join(f"{_clock(b.start_time)} – {_clock(b.end_time)}" for b in blocks)
        return f"That time is outside your {name} hours ({hours}). Pick a time within them."
    if t1 is None:
        return "None of these dates fall on your working days, so there's nothing to block."
    return "That time is outside your working hours on every date in this range."


def block_window(block):
    """[start, end) of the whole block as aware PH datetimes (first day's
    start to last day's end)."""
    ph = _ph()
    lo = datetime.combine(block.start_date, block.start_time or time(0), tzinfo=ph)
    if block.whole_day:
        hi = datetime.combine(block.end_date, time(0), tzinfo=ph) + timedelta(days=1)
    else:
        hi = datetime.combine(block.end_date, block.end_time, tzinfo=ph)
    return lo, hi


def conflicting_appointments(block):
    """Pending/confirmed consultations that fall inside the block's time."""
    from scheduling.models import Appointment
    from scheduling.serializers import DEFAULT_SESSION_MINUTES

    from .services import time_off_intervals

    lo, hi = block_window(block)
    intervals = time_off_intervals(block.rnd_id, lo, hi)
    out = []
    for a in (Appointment.objects.filter(relationship__rnd_id=block.rnd_id, status__in=["pending", "confirmed"],
                                         scheduled_at__lt=hi, scheduled_at__gte=lo - timedelta(hours=3))
              .select_related("relationship__client").order_by("scheduled_at")):
        a_end = a.scheduled_at + timedelta(minutes=a.duration_minutes or DEFAULT_SESSION_MINUTES)
        if any(s < a_end and e > a.scheduled_at for s, e in intervals):
            out.append({"id": a.id, "scheduled_at": a.scheduled_at, "status": a.status,
                        "type_label": a.get_type_display(), "client_name": a.relationship.client.full_name})
    return out


class RndTimeOffListCreateView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        today = timezone.now().astimezone(_ph()).date()
        blocks = RndTimeOff.objects.filter(rnd=request.user, end_date__gte=today)
        return Response(RndTimeOffSerializer(blocks, many=True).data)

    def post(self, request):
        data = RndTimeOffSerializer(data=request.data, context={"rnd": request.user})
        data.is_valid(raise_exception=True)
        block = data.save(rnd=request.user)
        return Response({**RndTimeOffSerializer(block).data, "conflicts": conflicting_appointments(block)},
                        status=status.HTTP_201_CREATED)


class RndTimeOffDetailView(APIView):
    permission_classes = [IsRnd]

    def delete(self, request, pk):
        get_object_or_404(RndTimeOff, pk=pk, rnd=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
