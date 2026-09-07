from rest_framework import serializers

from accounts.serializers import UserSerializer
from scheduling.models import RndClientRelationship, Review

from .models import ClientHealthProfile, ClientProfile, RndAvailabilitySchedule, RndLanguage, RndProfile


class PublicReviewSerializer(serializers.ModelSerializer):
    """Reviews shown on an RND's public profile — first name + last-initial
    only, not the full UserSerializer, per this project's PII-minimization
    pattern (RA 10173)."""

    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "client_name", "rating", "comment", "created_at"]

    def get_client_name(self, obj):
        last_initial = f"{obj.client.last_name[0]}." if obj.client.last_name else ""
        return f"{obj.client.first_name} {last_initial}".strip()


class RndLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RndLanguage
        fields = ["id", "language_code", "language_name"]


class RndAvailabilityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RndAvailabilitySchedule
        fields = [
            "id", "day_of_week", "start_time", "end_time",
            "is_available", "effective_from", "effective_to",
        ]

    def validate(self, attrs):
        # Only enforced when both are present in this request — on a PATCH
        # that only touches one field, fall back to the existing instance's
        # other value so a partial update can't accidentally bypass this.
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start is not None and end is not None and end <= start:
            raise serializers.ValidationError("End time must be after start time.")
        return attrs


class RndProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    languages = RndLanguageSerializer(source="user.languages", many=True, read_only=True)
    relationship_status = serializers.SerializerMethodField()

    class Meta:
        model = RndProfile
        fields = [
            "id", "user", "prc_license_number", "prc_expiry_date", "specialization",
            "language_codes", "bio", "consultation_fee", "available_for_new_clients",
            "is_verified", "verified_at", "languages", "relationship_status",
        ]
        read_only_fields = ["is_verified", "verified_at"]

    def get_relationship_status(self, obj):
        """The requesting client's relationship with this RND, if any —
        None for non-client requesters (RND viewing another RND's public
        profile, admin) so Find an RND's "Request" button reflects real
        backend state instead of only what happened in the current page
        visit (it previously never checked this at all)."""
        request = self.context.get("request")
        if not request or getattr(request.user, "role", None) != "client":
            return None
        rel = RndClientRelationship.objects.filter(rnd=obj.user, client=request.user).first()
        return rel.status if rel else None


class RndProfileUpdateSerializer(serializers.ModelSerializer):
    """For the RND editing their own profile — excludes verification fields."""

    class Meta:
        model = RndProfile
        fields = ["specialization", "language_codes", "bio", "consultation_fee", "available_for_new_clients"]


class ClientHealthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientHealthProfile
        fields = [
            "id", "medical_conditions", "allergies",
            "dietary_restrictions", "health_goals", "religion", "notes",
        ]


class ClientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    health_profile = ClientHealthProfileSerializer(source="user.health_profile", read_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            "id", "user", "date_of_birth", "sex", "language_code",
            "address", "emergency_contact", "emergency_phone", "health_profile",
        ]


class ClientProfileUpdateSerializer(serializers.ModelSerializer):
    """For the client editing their own profile — excludes the linked user."""

    class Meta:
        model = ClientProfile
        fields = ["date_of_birth", "sex", "language_code", "address", "emergency_contact", "emergency_phone"]
