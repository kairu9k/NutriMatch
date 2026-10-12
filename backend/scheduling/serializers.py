from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer
from profiles.models import RndProfile

from .models import Appointment, ConsultationSession, Review, RndClientRelationship


class RndClientRelationshipSerializer(serializers.ModelSerializer):
    rnd = UserSerializer(read_only=True)
    client = UserSerializer(read_only=True)

    class Meta:
        model = RndClientRelationship
        fields = ["id", "rnd", "client", "status", "started_at", "ended_at", "notes", "created_at"]
        read_only_fields = ["status", "started_at", "ended_at"]

    # What anyone but the people involved may see of each other: the client
    # only gets the RND's public details (same rule as profiles/public.py),
    # the treating RND keeps the client's contact details.
    PUBLIC_PERSON = ("id", "first_name", "last_name", "profile_photo", "role")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        viewer = getattr(request, "user", None)
        viewer_id = getattr(viewer, "id", None)
        is_admin = getattr(viewer, "role", None) == "admin"
        if not is_admin and viewer_id != instance.rnd_id:
            data["rnd"] = {k: v for k, v in (data.get("rnd") or {}).items() if k in self.PUBLIC_PERSON}
        if not is_admin and viewer_id not in (instance.rnd_id, instance.client_id):
            data["client"] = {k: v for k, v in (data.get("client") or {}).items() if k in self.PUBLIC_PERSON}
        return data


class ConsultationSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationSession
        fields = [
            "id", "video_provider", "session_status",
            "session_started_at", "session_ended_at", "actual_duration_min",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    relationship = RndClientRelationshipSerializer(read_only=True)
    consultation_sessions = ConsultationSessionSerializer(many=True, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "relationship", "scheduled_at", "type", "status", "duration_minutes",
            "video_session_url", "meeting_id", "cancellation_reason", "notes",
            "consultation_sessions", "created_at",
        ]
        read_only_fields = ["status", "video_session_url", "meeting_id"]

    def to_representation(self, instance):
        """Adds `payment` ({invoice_id, status, amount} or None). The video
        link and room name are only included for the RND, or for the client
        once the appointment is paid — hidden by default when the viewer is
        unknown, so the room can't be joined before paying."""
        from billing.services import appointment_invoice

        data = super().to_representation(instance)
        invoice = appointment_invoice(instance)
        data["payment"] = (
            {"invoice_id": invoice.id, "status": invoice.status, "amount": str(invoice.amount)} if invoice else None
        )
        # Join window: the room opens JOIN_EARLY_MINUTES before the start and
        # closes JOIN_LATE_MINUTES after the scheduled end.
        start = instance.scheduled_at
        end = start + timedelta(minutes=instance.duration_minutes or DEFAULT_SESSION_MINUTES)
        opens_at = start - timedelta(minutes=JOIN_EARLY_MINUTES)
        closes_at = end + timedelta(minutes=JOIN_LATE_MINUTES)
        data["join_opens_at"] = opens_at.isoformat()
        data["join_closes_at"] = closes_at.isoformat()

        request = self.context.get("request")
        viewer_id = getattr(getattr(request, "user", None), "id", None)
        is_rnd_viewer = viewer_id is not None and viewer_id == instance.relationship.rnd_id
        paid = invoice is not None and invoice.status == "paid"
        in_window = opens_at <= timezone.now() <= closes_at
        # The client only gets the room once it's paid AND within the join
        # window (the RND always sees it, to prepare).
        if not (is_rnd_viewer or (paid and in_window and instance.status == "confirmed")):
            data["video_session_url"] = None
            data["meeting_id"] = None
        return data


DEFAULT_SESSION_MINUTES = 60
JOIN_EARLY_MINUTES = 15
JOIN_LATE_MINUTES = 15
MIN_SESSION_MINUTES = 15
MAX_SESSION_MINUTES = 120
PH_TZ = ZoneInfo("Asia/Manila")
ACTIVE_STATUSES = ("pending", "confirmed")


def overlapping_appointments(start, end, **scope):
    """Pending/confirmed appointments (within `scope`) whose time overlaps
    [start, end). Durations vary, so candidates are narrowed in SQL and the
    exact overlap is checked in Python."""
    candidates = Appointment.objects.filter(
        status__in=ACTIVE_STATUSES,
        scheduled_at__lt=end,
        scheduled_at__gt=start - timedelta(minutes=MAX_SESSION_MINUTES),
        **scope,
    )
    ids = [
        a.id for a in candidates
        if a.scheduled_at + timedelta(minutes=a.duration_minutes or DEFAULT_SESSION_MINUTES) > start
    ]
    return Appointment.objects.filter(id__in=ids)


def fits_rnd_availability(rnd_id, start, end):
    """True when [start, end) sits inside one of the RND's weekly available
    blocks (Philippine time). An RND with no schedule set isn't restricted."""
    from profiles.models import RndAvailabilitySchedule

    schedules = RndAvailabilitySchedule.objects.filter(rnd_id=rnd_id, is_available=True)
    if not schedules.exists():
        return True
    local_start, local_end = start.astimezone(PH_TZ), end.astimezone(PH_TZ)
    if local_start.date() != local_end.date():
        return False
    day = local_start.date()
    weekday = (day.weekday() + 1) % 7  # Python Monday=0 -> model Sunday=0
    for block in schedules.filter(day_of_week=weekday):
        if block.effective_from and block.effective_from > day:
            continue
        if block.effective_to and block.effective_to < day:
            continue
        if block.start_time <= local_start.time() and local_end.time() <= block.end_time:
            return True
    return False


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Clients book any verified RND directly — there's no separate
    request/accept step. A first booking creates the relationship as
    'pending'; RndAppointmentConfirmView activates it when the RND confirms."""

    rnd_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = ["rnd_id", "scheduled_at", "type", "duration_minutes", "notes"]

    def validate_rnd_id(self, value):
        from profiles.services import bookable_rnd_profiles

        if not RndProfile.objects.filter(user_id=value, is_verified=True).exists():
            raise serializers.ValidationError("RND not found.")
        profile = bookable_rnd_profiles().filter(user_id=value).first()
        if not profile:
            raise serializers.ValidationError("This RND isn't taking bookings yet.")
        self._rnd_profile = profile
        return value

    def validate_duration_minutes(self, value):
        if value is not None and not (MIN_SESSION_MINUTES <= value <= MAX_SESSION_MINUTES):
            raise serializers.ValidationError(
                f"A consultation must be {MIN_SESSION_MINUTES}-{MAX_SESSION_MINUTES} minutes long."
            )
        return value

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Pick a time in the future.")
        return value

    def validate(self, attrs):
        client = self.context["request"].user
        if client.onboarding_completed_at is None:
            raise serializers.ValidationError(
                "Finish setting up your account (health background and screening) before booking."
            )
        profile = self._rnd_profile
        # One RND at a time: a different RND only after the current one discharges them.
        from .services import current_rnd_relationship

        current = current_rnd_relationship(client, exclude_rnd_id=profile.user_id)
        if current:
            name = current.rnd.full_name
            raise serializers.ValidationError(
                f"You're under RND {name}'s care. You can book a different RND once RND {name} discharges you."
                if current.status == RndClientRelationship.Status.ACTIVE else
                f"You have a booking waiting for RND {name}. Cancel it first if you'd like a different RND."
            )
        relationship = RndClientRelationship.objects.filter(rnd_id=profile.user_id, client=client).first()
        is_existing_client = relationship is not None and relationship.status == RndClientRelationship.Status.ACTIVE
        if not profile.available_for_new_clients and not is_existing_client:
            raise serializers.ValidationError("This RND isn't accepting new clients right now.")
        if attrs.get("type", Appointment.Type.VIDEO) not in (profile.consultation_modes or []):
            raise serializers.ValidationError({"type": ["This RND doesn't offer that consultation format."]})
        if attrs.get("type") == Appointment.Type.IN_PERSON and not (profile.clinic_address or "").strip():
            raise serializers.ValidationError({"type": ["This RND hasn't added a clinic address yet, so in-person consultations can't be booked."]})

        # The booking modal only offers open slots inside the RND's hours, but
        # the API enforces the same rules so they can't be bypassed.
        start = attrs["scheduled_at"]
        end = start + timedelta(minutes=attrs.get("duration_minutes") or DEFAULT_SESSION_MINUTES)
        if not fits_rnd_availability(profile.user_id, start, end):
            raise serializers.ValidationError(
                {"scheduled_at": ["That time is outside the RND's available hours. Please pick one of the listed times."]}
            )
        if overlapping_appointments(start, end, relationship__rnd_id=profile.user_id).exists():
            raise serializers.ValidationError({"scheduled_at": ["That time was just booked. Please pick another slot."]})
        if overlapping_appointments(start, end, relationship__client=client).exists():
            raise serializers.ValidationError({"scheduled_at": ["You already have an appointment at that time."]})
        return attrs

    def create(self, validated_data):
        rnd_id = validated_data.pop("rnd_id")
        client = self.context["request"].user
        relationship, _ = RndClientRelationship.objects.get_or_create(
            rnd_id=rnd_id, client=client,
            defaults={"status": RndClientRelationship.Status.PENDING},
        )
        if relationship.status == RndClientRelationship.Status.DISCHARGED:
            relationship.status = RndClientRelationship.Status.PENDING
            relationship.ended_at = None
            relationship.save(update_fields=["status", "ended_at", "updated_at"])
        return Appointment.objects.create(relationship=relationship, **validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    # The 1-5 range is also a DB constraint; validating here returns a clear
    # 400 instead of an IntegrityError (500).
    rating = serializers.IntegerField(
        min_value=1, max_value=5,
        error_messages={"min_value": "Choose a rating from 1 to 5 stars.", "max_value": "Choose a rating from 1 to 5 stars."},
    )
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Review
        fields = ["id", "appointment", "client", "rnd", "rating", "comment", "is_public", "created_at"]
        read_only_fields = ["client", "rnd"]

    def validate_appointment(self, value):
        request = self.context["request"]
        if value.relationship.client_id != request.user.id:
            raise serializers.ValidationError("You can only review your own appointments.")
        if value.status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError("You can only review completed appointments.")
        if hasattr(value, "review"):
            raise serializers.ValidationError("This appointment has already been reviewed.")
        return value

    def create(self, validated_data):
        appointment = validated_data["appointment"]
        return Review.objects.create(
            client=self.context["request"].user,
            rnd_id=appointment.relationship.rnd_id,
            **validated_data,
        )


class ClientReviewListSerializer(serializers.ModelSerializer):
    """Reviews the logged-in client has left — mirrors ReviewSerializer's
    shape but nests rnd instead of client, since a client's own view has
    no use for re-displaying their own identity."""

    rnd = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "appointment", "rnd", "rating", "comment", "created_at"]
        read_only_fields = fields
