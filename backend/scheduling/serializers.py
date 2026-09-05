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
