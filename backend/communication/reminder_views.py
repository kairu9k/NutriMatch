"""Reminder settings (client) and RND-set reminders (RND, per client)."""

from datetime import date, datetime, time

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import RndClientRelationship

from .models import Reminder, ReminderPreference
from .reminders import first_occurrence, ph_tz, run_for_client_throttled, today_items


class ReminderPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderPreference
        fields = ["appointments", "payments", "meal_logging", "rnd_reminders", "email", "updated_at"]
        read_only_fields = ["updated_at"]


class ReminderSerializer(serializers.ModelSerializer):
    """An RND-set reminder. `date` + `time` are Philippine time; `send_at`
    is the next time it fires."""

    date = serializers.DateField(write_only=True, required=False)
    time = serializers.TimeField(write_only=True, required=False, format="%H:%M")
    next_at = serializers.DateTimeField(source="send_at", read_only=True)
    time_of_day = serializers.SerializerMethodField()
    repeat_label = serializers.CharField(source="get_repeat_display", read_only=True)
    type_label = serializers.CharField(source="get_type_display", read_only=True)
    done = serializers.BooleanField(source="is_sent", read_only=True)
    done_today = serializers.SerializerMethodField()  # ticked off in My tasks today
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    def get_done_today(self, obj):
        return obj.done_on is not None and obj.done_on == timezone.now().astimezone(ph_tz()).date()

    class Meta:
        model = Reminder
        fields = [
            "id", "title", "message", "type", "type_label", "repeat", "repeat_label", "date", "time", "next_at",
            "time_of_day", "is_active", "is_muted", "last_sent_at", "done", "done_today", "created_by_name", "created_at",
        ]
        read_only_fields = ["is_muted", "last_sent_at"]

    def get_time_of_day(self, obj):
        return obj.send_at.astimezone(ph_tz()).strftime("%H:%M")

    def validate_type(self, value):
        if value not in (Reminder.Type.MEDICATION, Reminder.Type.GENERAL):
            raise serializers.ValidationError("Choose medication or general.")
        return value

    def validate_title(self, value):
        value = (value or "").strip()
        if len(value) < 3:
            raise serializers.ValidationError("Give the reminder a short title.")
        return value

    def validate(self, attrs):
        inst = self.instance
        if inst is None and ("date" not in attrs or "time" not in attrs):
            raise serializers.ValidationError({"time": ["Pick when the reminder starts."]})
        if "date" in attrs or "time" in attrs or "repeat" in attrs:
            local = inst.send_at.astimezone(ph_tz()) if inst else None
            d = attrs.pop("date", None) or (local.date() if local else date.today())
            t = attrs.pop("time", None) or (local.timetz().replace(tzinfo=None) if local else time(8))
            repeat = attrs.get("repeat", inst.repeat if inst else Reminder.Repeat.ONCE)
            start = first_occurrence(repeat, datetime.combine(d, t, tzinfo=ph_tz()))
            if repeat == Reminder.Repeat.ONCE and start <= timezone.now():
                raise serializers.ValidationError({"time": ["A one-time reminder has to be in the future."]})
            if repeat != Reminder.Repeat.ONCE:
                # a repeating reminder that starts in the past begins at its next time
                from .reminders import next_occurrence

                probe = Reminder(send_at=start, repeat=repeat)
                if start <= timezone.now():
                    start = next_occurrence(probe, timezone.now())
            attrs["send_at"] = start
            attrs["is_sent"] = False
        return attrs


# ------------------------------------------------------------- client
class ClientReminderSettingsView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        return Response(ReminderPreferenceSerializer(ReminderPreference.for_user(request.user)).data)

    def put(self, request):
        pref = ReminderPreference.for_user(request.user)
        s = ReminderPreferenceSerializer(pref, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


class ClientReminderListView(APIView):
    """Tasks for the client (not finished one-offs): set by their RNDs, or
    their own (POST — "+ Add a task" in My tasks)."""

    permission_classes = [IsClient]

    def get(self, request):
        from django.db.models import Q

        qs = (Reminder.objects.filter(client=request.user, created_by__isnull=False, is_sent=False)
              .filter(Q(relationship__status=RndClientRelationship.Status.ACTIVE) | Q(relationship__isnull=True, created_by=request.user))
              .select_related("created_by").order_by("send_at"))
        return Response(ReminderSerializer(qs, many=True).data)

    def post(self, request):
        s = ReminderSerializer(data={**request.data, "type": Reminder.Type.GENERAL})
        s.is_valid(raise_exception=True)
        r = s.save(client=request.user, created_by=request.user, relationship=None)
        return Response(ReminderSerializer(r).data, status=status.HTTP_201_CREATED)


class ClientReminderMuteView(APIView):
    """PATCH {is_muted} mutes a task; DELETE removes one of the client's own."""

    permission_classes = [IsClient]

    def patch(self, request, pk):
        r = get_object_or_404(Reminder, pk=pk, client=request.user, created_by__isnull=False)
        r.is_muted = bool(request.data.get("is_muted"))
        r.save(update_fields=["is_muted"])
        return Response(ReminderSerializer(r).data)

    def delete(self, request, pk):
        get_object_or_404(Reminder, pk=pk, client=request.user, created_by=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientTaskCheckView(APIView):
    """POST {done: true|false} ticks a task off for today in My tasks."""

    permission_classes = [IsClient]

    def post(self, request, pk):
        r = get_object_or_404(Reminder, pk=pk, client=request.user, created_by__isnull=False)
        today = timezone.now().astimezone(ph_tz()).date()
        r.done_on = today if request.data.get("done", True) else None
        r.save(update_fields=["done_on"])
        return Response({"id": r.id, "done": r.done_on == today})


class ClientTodayView(APIView):
    """Dashboard "Coming up today" — also sends anything due right now."""

    permission_classes = [IsClient]

    def get(self, request):
        run_for_client_throttled(request.user)
        return Response(today_items(request.user))


# ------------------------------------------------------------- RND
def _rnd_relationship(request, rel_id):
    return get_object_or_404(RndClientRelationship, pk=rel_id, rnd=request.user)


class RndClientReminderListCreateView(APIView):
    permission_classes = [IsRnd]

    def get(self, request, relationship_id):
        rel = _rnd_relationship(request, relationship_id)
        qs = Reminder.objects.filter(relationship=rel, created_by__isnull=False).select_related("created_by").order_by("is_sent", "send_at")
        return Response(ReminderSerializer(qs, many=True).data)

    def post(self, request, relationship_id):
        from .services import notify

        rel = _rnd_relationship(request, relationship_id)
        if rel.status != RndClientRelationship.Status.ACTIVE:
            return Response({"detail": "You can only set reminders for active clients."}, status=status.HTTP_400_BAD_REQUEST)
        s = ReminderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        r = s.save(client=rel.client, relationship=rel, created_by=request.user)
        when = r.send_at.astimezone(ph_tz())
        notify(recipient=rel.client, notifiable_type="reminder", notifiable_id=r.id, subject="New reminder from your RND",
               content=f"RND {request.user.full_name} set a reminder for you: \"{r.title}\" — {r.get_repeat_display().lower()} at "
                       f"{when.hour % 12 or 12}:{when:%M} {when:%p}. You can mute it in Profile Settings.")
        return Response(ReminderSerializer(r).data, status=status.HTTP_201_CREATED)


class RndReminderDetailView(APIView):
    permission_classes = [IsRnd]

    def _get(self, request, pk):
        return get_object_or_404(Reminder, pk=pk, created_by=request.user)

    def patch(self, request, pk):
        r = self._get(request, pk)
        s = ReminderSerializer(r, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    def delete(self, request, pk):
        self._get(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
