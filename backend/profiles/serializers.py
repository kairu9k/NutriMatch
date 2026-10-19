from django.db.models import Avg, Count
from rest_framework import serializers

from accounts.serializers import UserSerializer
from scheduling.models import Review

from .models import (
    CONSULTATION_MODES,
    LANGUAGE_NAMES,
    LANGUAGES,
    MIN_CONSULTATION_FEE,
    ClientHealthProfile,
    ClientProfile,
    RndAvailabilitySchedule,
    RndLanguage,
    RndProfile,
)


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
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = RndProfile
        fields = [
            "id", "user", "prc_license_number", "prc_expiry_date", "specialization",
            "language_codes", "bio", "consultation_fee", "consultation_modes", "available_for_new_clients",
            "is_verified", "verified_at", "languages", "average_rating", "review_count", "clinic_address",
        ]
        # PRC details are set at registration and checked by the admin —
        # never editable by the RND (Profile Settings shows them read-only).
        read_only_fields = ["is_verified", "verified_at", "prc_license_number", "prc_expiry_date"]

    def _review_aggregate(self, obj):
        if not hasattr(obj, "_review_aggregate_cache"):
            obj._review_aggregate_cache = Review.objects.filter(
                rnd_id=obj.user_id, is_public=True
            ).aggregate(avg_rating=Avg("rating"), review_count=Count("id"))
        return obj._review_aggregate_cache

    def get_average_rating(self, obj):
        return self._review_aggregate(obj)["avg_rating"]

    def get_review_count(self, obj):
        return self._review_aggregate(obj)["review_count"]


class MyRndProfileSerializer(RndProfileSerializer):
    """The RND's own profile (GET/PATCH /api/rnd/profile/) — adds a
    short-lived signed link to their own PRC license photo for the
    read-only PRC section in Profile Settings. Never used for client-facing
    RND search/detail: the photo is private (RA 10173)."""

    prc_license_image_url = serializers.SerializerMethodField()

    class Meta(RndProfileSerializer.Meta):
        fields = RndProfileSerializer.Meta.fields + ["prc_license_image_url"]

    def get_prc_license_image_url(self, obj):
        from .services import prc_license_image_url

        return prc_license_image_url(obj.prc_license_image)


class RndProfileUpdateSerializer(serializers.ModelSerializer):
    """For the RND editing their own profile — excludes verification fields.
    `languages` (codes from LANGUAGES) replaces their RndLanguage rows."""

    languages = serializers.ListField(child=serializers.CharField(max_length=10), required=False, write_only=True, max_length=len(LANGUAGES))

    class Meta:
        model = RndProfile
        fields = [
            "specialization", "language_codes", "bio", "consultation_fee",
            "consultation_modes", "available_for_new_clients", "languages", "clinic_address",
        ]
        # Specialization is picked at registration (from RND_SPECIALIZATIONS) and
        # changed only by an admin (Edit details) — shown read-only to the RND.
        read_only_fields = ["specialization"]

    def validate_clinic_address(self, value):
        value = (value or "").strip()
        if value and len(value) < 10:
            raise serializers.ValidationError("Enter the full address — building, street, barangay and city.")
        return value or None

    def validate(self, attrs):
        # Checked when formats or the address are being saved (the Professional
        # Profile form), so an unrelated edit (e.g. languages) never gets stuck.
        if "consultation_modes" not in attrs and "clinic_address" not in attrs:
            return attrs
        modes = attrs.get("consultation_modes", getattr(self.instance, "consultation_modes", None)) or []
        address = attrs["clinic_address"] if "clinic_address" in attrs else getattr(self.instance, "clinic_address", None)
        if "in_person" in modes and not address:
            raise serializers.ValidationError({"clinic_address": ["Add your clinic address — clients need to know where to go for in-person consultations."]})
        return attrs

    def validate_consultation_fee(self, value):
        if value < MIN_CONSULTATION_FEE:
            raise serializers.ValidationError(f"The consultation fee must be at least \u20b1{MIN_CONSULTATION_FEE}.")
        return value

    def validate_bio(self, value):
        value = (value or "").strip()
        if len(value) < 50:
            raise serializers.ValidationError("Write at least 50 characters — clients read this before booking.")
        return value

    def validate_languages(self, value):
        codes = list(dict.fromkeys(value))
        if any(code not in LANGUAGE_NAMES for code in codes):
            raise serializers.ValidationError("Unknown language.")
        if not codes:
            raise serializers.ValidationError("Keep at least one language.")
        return codes

    def update(self, instance, validated_data):
        from .services import set_rnd_languages

        languages = validated_data.pop("languages", None)
        instance = super().update(instance, validated_data)
        if languages is not None:
            set_rnd_languages(instance.user, languages)
            instance.language_codes = languages
            instance.save(update_fields=["language_codes"])
        return instance

    def validate_consultation_modes(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Offer at least one consultation mode.")
        invalid = [m for m in value if m not in CONSULTATION_MODES]
        if invalid:
            raise serializers.ValidationError(f"Unknown mode(s): {', '.join(map(str, invalid))}.")
        # Keep a stable order and drop duplicates.
        return [m for m in CONSULTATION_MODES if m in value]


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
    """For the client editing their own profile — excludes the linked user.
    medical_conditions lives on ClientHealthProfile; the first entry is the
    primary condition shown on the RND's patient list and client chart."""

    medical_conditions = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=True), required=False, allow_empty=True, max_length=10,
        write_only=True,
    )

    # Health background (onboarding + Profile Settings). allergies [] means
    # "no food allergies" (answered); null means not answered yet.
    allergies = serializers.ListField(child=serializers.CharField(max_length=60), required=False, allow_empty=True, max_length=15, write_only=True)
    dietary_restrictions = serializers.ListField(child=serializers.CharField(max_length=60), required=False, allow_empty=True, max_length=15, write_only=True)
    health_goals = serializers.ListField(child=serializers.CharField(max_length=100), required=False, allow_empty=True, max_length=10, write_only=True)
    religion = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            "date_of_birth", "sex", "language_code", "address", "emergency_contact", "emergency_phone",
            "medical_conditions", "allergies", "dietary_restrictions", "health_goals", "religion",
        ]

    @staticmethod
    def _clean_list(values):
        cleaned = []
        for item in values:
            item = item.strip()
            if item and item.lower() not in {c.lower() for c in cleaned}:
                cleaned.append(item)
        return cleaned

    def validate_allergies(self, value):
        return self._clean_list(value)

    def validate_dietary_restrictions(self, value):
        return self._clean_list(value)

    def validate_health_goals(self, value):
        return self._clean_list(value)

    def validate_medical_conditions(self, value):
        cleaned = []
        for item in value:
            item = item.strip()
            if item and item.lower() not in {c.lower() for c in cleaned}:
                cleaned.append(item)
        return cleaned

    def update(self, instance, validated_data):
        conditions = validated_data.pop("medical_conditions", None)
        health_updates = {
            key: validated_data.pop(key) for key in ("allergies", "dietary_restrictions", "health_goals", "religion")
            if key in validated_data
        }
        instance = super().update(instance, validated_data)
        if conditions is not None or health_updates:
            health_profile, _ = ClientHealthProfile.objects.get_or_create(user=instance.user)
            fields = ["updated_at"]
            if conditions is not None:
                health_profile.medical_conditions = conditions or None
                fields.append("medical_conditions")
            for key, value in health_updates.items():
                # allergies keeps [] ("none") — it's the onboarding answer
                setattr(health_profile, key, value if (value or key == "allergies") else None)
                fields.append(key)
            health_profile.save(update_fields=fields)
        return instance

    def validate_date_of_birth(self, value):
        from accounts.validators import validate_client_birth_date

        return validate_client_birth_date(value)
