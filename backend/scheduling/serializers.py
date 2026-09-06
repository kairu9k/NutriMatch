from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Appointment, ConsultationSession, Review, RndClientRelationship


class RndClientRelationshipSerializer(serializers.ModelSerializer):
    rnd = UserSerializer(read_only=True)
    client = UserSerializer(read_only=True)

    class Meta:
        model = RndClientRelationship
        fields = ["id", "rnd", "client", "status", "started_at", "ended_at", "notes", "created_at"]
        read_only_fields = ["status", "started_at", "ended_at"]


class RndPatientListSerializer(serializers.ModelSerializer):
    """One row per relationship for the RND's patient list — condition and
    visit/NCP summaries computed from prefetched querysets set by the view
    (get_queryset annotates `_appointments`/`_ncp_records`), so this stays
    one query for the relationships plus the prefetches, not N+1."""

    client = UserSerializer(read_only=True)
    condition = serializers.SerializerMethodField()
    last_visit = serializers.SerializerMethodField()
    next_appointment = serializers.SerializerMethodField()
    ncp_status = serializers.SerializerMethodField()

    class Meta:
        model = RndClientRelationship
        fields = [
            "id", "client", "status", "condition",
            "last_visit", "next_appointment", "ncp_status", "created_at",
        ]

    def get_condition(self, obj):
        health_profile = getattr(obj.client, "health_profile", None)
        conditions = getattr(health_profile, "medical_conditions", None)
        return conditions[0] if conditions else None

    def _appointments(self, obj):
        return list(getattr(obj, "_prefetched_appointments", []))

    def get_last_visit(self, obj):
        completed = [a for a in self._appointments(obj) if a.status == Appointment.Status.COMPLETED]
        if not completed:
            return None
        return max(completed, key=lambda a: a.scheduled_at).scheduled_at

    def get_next_appointment(self, obj):
        now = timezone.now()
        upcoming = [
            a for a in self._appointments(obj)
            if a.status in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED) and a.scheduled_at > now
        ]
        if not upcoming:
            return None
        return min(upcoming, key=lambda a: a.scheduled_at).scheduled_at

    def get_ncp_status(self, obj):
        records = list(getattr(obj, "_prefetched_ncp_records", []))
        if not records:
            return "not_started"
        latest = max(records, key=lambda r: r.created_at)
        return latest.status


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


class AppointmentCreateSerializer(serializers.ModelSerializer):
    rnd_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = ["rnd_id", "scheduled_at", "type", "duration_minutes", "notes"]

    def validate_rnd_id(self, value):
        client = self.context["request"].user
        relationship = RndClientRelationship.objects.filter(
            rnd_id=value, client=client, status=RndClientRelationship.Status.ACTIVE
        ).first()
        if not relationship:
            raise serializers.ValidationError(
                "You must have an active relationship with this RND before booking."
            )
        self._relationship = relationship
        return value

    def create(self, validated_data):
        validated_data.pop("rnd_id")
        return Appointment.objects.create(relationship=self._relationship, **validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)

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
