import re

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from profiles.models import MIN_CONSULTATION_FEE, RND_SPECIALIZATIONS, ClientHealthProfile, ClientProfile, RndProfile
from profiles.services import (
    ALLOWED_LICENSE_IMAGE_TYPES,
    MAX_LICENSE_IMAGE_BYTES,
    LicenseImageUploadError,
    prc_license_image_url,
    upload_prc_license_image,
)

from .models import User
from .services import send_verification_code
from .validators import validate_client_birth_date, validate_person_name, validate_rnd_birth_date


class JsonListField(serializers.ListField):
    """A list that may also arrive as a JSON string (multipart forms send
    complex fields that way)."""

    def to_internal_value(self, data):
        import json

        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], str) and data[0].startswith("["):
            data = data[0]  # QueryDict hands a single value back as a list
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                raise serializers.ValidationError("Invalid list.")
        if not isinstance(data, list):
            raise serializers.ValidationError("Expected a list.")
        return data


class RegistrationConsentMixin(serializers.Serializer):
    """Both registration forms: the person must agree to the Terms & Privacy
    Policy and consent to their personal and health data being processed for
    nutrition care (RA 10173 informed consent). Recorded on the account and in
    the audit log by record_consent()."""

    accept_terms = serializers.BooleanField(write_only=True)
    data_privacy_consent = serializers.BooleanField(write_only=True)

    def validate_accept_terms(self, value):
        if value is not True:
            raise serializers.ValidationError("You must agree to the Terms and Conditions and Privacy Policy.")
        return value

    def validate_data_privacy_consent(self, value):
        if value is not True:
            raise serializers.ValidationError("You must consent to the processing of your personal and health data.")
        return value

    def record_consent(self, user):
        from django.utils import timezone

        from core.models import AuditLog

        now = timezone.now()
        user.terms_accepted_at = now
        user.data_consent_at = now
        user.save(update_fields=["terms_accepted_at", "data_consent_at"])
        request = self.context.get("request")
        AuditLog.objects.create(
            user=user,
            action="consent.given",
            table_name="users",
            record_id=user.id,
            new_values={"terms_and_privacy_policy": True, "data_processing_consent": True, "role": user.role},
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:255] if request else None),
        )


class ReplaceUnverifiedAccountMixin(serializers.Serializer):
    """An email that belongs to a *verified* account can't register again.
    One whose earlier signup was never verified can: that unfinished account
    (which can't log in) is replaced by the new registration — otherwise a
    typo'd or abandoned signup would lock the person's email out for good."""

    def validate_email(self, value):
        existing = User.objects.filter(email__iexact=value).first()
        if existing is None:
            return value
        rejected_rnd = (
            existing.role == User.Role.RND
            and getattr(getattr(existing, "rnd_profile", None), "review_status", None) == "rejected"
        )
        if (existing.email_verified_at is not None and not rejected_rnd) or existing.role == User.Role.ADMIN:
            raise serializers.ValidationError("An account with this email already exists.")
        # An unfinished (unverified) signup, or an RND application that wasn't
        # approved, is replaced by this new registration.
        self._unverified_to_replace = existing
        return value

    def remove_unverified_account(self):
        """Call inside create(), before creating the new user."""
        old = getattr(self, "_unverified_to_replace", None)
        if old is None:
            return
        license_id = getattr(getattr(old, "rnd_profile", None), "prc_license_image", None)
        old.delete()
        if license_id:
            from django.db import transaction as db_transaction

            db_transaction.on_commit(lambda: _destroy_license_image(license_id))


def _destroy_license_image(public_id):
    """Best-effort cleanup of a replaced signup's private PRC photo."""
    try:
        import cloudinary.uploader

        from profiles.services import _configure

        _configure()
        cloudinary.uploader.destroy(public_id, type="authenticated", invalidate=True)
    except Exception:
        pass


class PersonNameFieldsMixin:
    """first_name / last_name: letters only (see validate_person_name)."""

    def validate_first_name(self, value):
        return validate_person_name(value)

    def validate_last_name(self, value):
        return validate_person_name(value)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "phone", "profile_photo", "is_active", "created_at", "onboarding_completed_at", "welcome_seen_at",
        ]
        read_only_fields = fields


class MeUpdateSerializer(PersonNameFieldsMixin, serializers.ModelSerializer):
    """Self-service edits. Email is deliberately excluded — changing it
    would bypass the email-verification gate login relies on."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]


class AdminClientListSerializer(serializers.ModelSerializer):
    """Admin-facing client list — condition/consultations/matched-RND are
    all derived from real relationship/appointment data via
    AdminClientListView's prefetches, same one-query-per-relation pattern
    as scheduling.RndPatientListSerializer. No "flagged" concept exists in
    the schema (the mockup's dispute-flag state has no backing model) —
    only real is_active is exposed, nothing fabricated."""

    condition = serializers.SerializerMethodField()
    consultations = serializers.SerializerMethodField()
    matched_rnd = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "is_active", "created_at", "profile_photo",
            "condition", "consultations", "matched_rnd", "last_active",
        ]
        read_only_fields = fields

    def get_condition(self, obj):
        health_profile = getattr(obj, "health_profile", None)
        conditions = getattr(health_profile, "medical_conditions", None)
        return conditions[0] if conditions else None

    def get_consultations(self, obj):
        return sum(len(getattr(rel, "_prefetched_appointments", [])) for rel in obj._prefetched_relationships)

    def get_matched_rnd(self, obj):
        active = [rel for rel in obj._prefetched_relationships if rel.status == "active"]
        return active[0].rnd.full_name if active else None

    def get_last_active(self, obj):
        all_appts = [a for rel in obj._prefetched_relationships for a in getattr(rel, "_prefetched_appointments", [])]
        if not all_appts:
            return None
        return max(a.scheduled_at for a in all_appts)


class AdminRndListSerializer(serializers.ModelSerializer):
    """Admin-facing RND list for RndVerification.vue — pending/verified
    RNDs in one view. patients/rating/revenue are all real, derived from
    prefetches on the view, and only meaningful once verified (a pending
    RND's application shows submitted-credential fields instead)."""

    prc_license_number = serializers.CharField(source="rnd_profile.prc_license_number", allow_null=True)
    prc_license_image_url = serializers.SerializerMethodField()
    specialization = serializers.CharField(source="rnd_profile.specialization")
    is_verified = serializers.BooleanField(source="rnd_profile.is_verified")
    verified_at = serializers.DateTimeField(source="rnd_profile.verified_at")
    submitted_at = serializers.DateTimeField(source="rnd_profile.created_at")
    review_status = serializers.CharField(source="rnd_profile.review_status")
    rejection_reason = serializers.CharField(source="rnd_profile.rejection_reason", allow_null=True)
    reviewed_at = serializers.DateTimeField(source="rnd_profile.reviewed_at")
    bio = serializers.CharField(source="rnd_profile.bio", allow_null=True)
    consultation_fee = serializers.DecimalField(source="rnd_profile.consultation_fee", max_digits=8, decimal_places=2)
    consultation_modes = serializers.JSONField(source="rnd_profile.consultation_modes")
    date_of_birth = serializers.DateField(source="rnd_profile.date_of_birth", allow_null=True)
    clinic_address = serializers.CharField(source="rnd_profile.clinic_address", allow_null=True)
    languages = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    patients = serializers.SerializerMethodField()
    consultations = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "first_name", "last_name", "email", "is_active", "created_at",
            "prc_license_number", "prc_license_image_url", "specialization", "is_verified", "verified_at",
            "submitted_at", "patients", "consultations", "average_rating", "revenue",
            "review_status", "rejection_reason", "reviewed_at", "bio", "consultation_fee", "consultation_modes",
            "date_of_birth", "languages", "availability", "profile_photo", "email_verified_at", "clinic_address",
        ]
        read_only_fields = fields

    def get_languages(self, obj):
        return [lang.language_name for lang in obj.languages.all()]

    def get_availability(self, obj):
        return [
            {"day_of_week": b.day_of_week, "start_time": b.start_time.strftime("%H:%M"), "end_time": b.end_time.strftime("%H:%M")}
            for b in obj.availability_schedules.filter(is_available=True).order_by("day_of_week", "start_time")
        ]

    def get_prc_license_image_url(self, obj):
        return prc_license_image_url(obj.rnd_profile.prc_license_image)

    def get_patients(self, obj):
        return len([rel for rel in getattr(obj, "_prefetched_relationships", []) if rel.status == "active"])

    def get_consultations(self, obj):
        return sum(
            len(getattr(rel, "_prefetched_completed_appointments", []))
            for rel in getattr(obj, "_prefetched_relationships", [])
        )

    def get_average_rating(self, obj):
        reviews = getattr(obj, "_prefetched_reviews", [])
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_revenue(self, obj):
        return sum(
            inv.amount
            for rel in getattr(obj, "_prefetched_relationships", [])
            for inv in getattr(rel, "_prefetched_paid_invoices", [])
        )


class RegisterClientSerializer(RegistrationConsentMixin, ReplaceUnverifiedAccountMixin, PersonNameFieldsMixin, serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    date_of_birth = serializers.DateField(validators=[validate_client_birth_date])
    sex = serializers.ChoiceField(choices=ClientProfile.Sex.choices, required=False, allow_null=True)
    primary_health_concern = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        health_concern = validated_data.pop("primary_health_concern", "")
        date_of_birth = validated_data.pop("date_of_birth", None)
        sex = validated_data.pop("sex", None)

        self.remove_unverified_account()
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.CLIENT,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        self.record_consent(user)
        ClientProfile.objects.create(user=user, date_of_birth=date_of_birth, sex=sex)
        # The sign-up "primary health concern" is the client's condition —
        # it's what the RND's patient list and client chart show. "Other"
        # carries no clinical meaning, so it's left for the client to specify
        # later in Profile Settings.
        has_condition = health_concern and health_concern.strip().lower() != "other"
        ClientHealthProfile.objects.create(
            user=user,
            medical_conditions=[health_concern.strip()] if has_condition else None,
            # Goals are the client's own picks in onboarding — the condition
            # isn't a goal (copying it here showed "Goals: Type 2 Diabetes").
        )
        send_verification_code(user)
        return user


class RegisterRndSerializer(RegistrationConsentMixin, ReplaceUnverifiedAccountMixin, PersonNameFieldsMixin, serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    prc_license_number = serializers.CharField(max_length=20)
    prc_license_image = serializers.FileField(write_only=True)
    date_of_birth = serializers.DateField(validators=[validate_rnd_birth_date])
    specialization = serializers.ChoiceField(choices=RND_SPECIALIZATIONS)
    # The rest of the application (reviewed by the admin before the RND can
    # sign in). List fields arrive as JSON strings in the multipart form.
    bio = serializers.CharField(min_length=50, max_length=1000, trim_whitespace=True, error_messages={
        "min_length": "Write at least 50 characters about your background and approach.",
        "blank": "Write a short professional bio.",
    })
    consultation_fee = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=MIN_CONSULTATION_FEE, max_value=100000, error_messages={
        "min_value": f"The consultation fee must be at least \u20b1{MIN_CONSULTATION_FEE}.",
    })
    consultation_modes = JsonListField()
    languages = JsonListField()
    # Optional: RNDs set their weekly hours in Profile Settings after approval.
    availability = JsonListField(required=False, default=list)
    profile_photo = serializers.FileField(write_only=True, required=False)
    # Required only when they offer in-person consultations.
    clinic_address = serializers.CharField(required=False, allow_blank=True, max_length=255, trim_whitespace=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        address = (attrs.get("clinic_address") or "").strip()
        if "in_person" in (attrs.get("consultation_modes") or []):
            if not address:
                raise serializers.ValidationError({"clinic_address": ["Add your clinic address — clients need to know where to go for in-person consultations."]})
            if len(address) < 10:
                raise serializers.ValidationError({"clinic_address": ["Enter the full address — building, street, barangay and city."]})
        attrs["clinic_address"] = address or None
        return attrs

    def validate_consultation_modes(self, value):
        from profiles.models import CONSULTATION_MODES

        if not value:
            raise serializers.ValidationError("Offer at least one consultation format.")
        if any(m not in CONSULTATION_MODES for m in value):
            raise serializers.ValidationError("Unknown consultation format.")
        return [m for m in CONSULTATION_MODES if m in value]

    def validate_languages(self, value):
        from profiles.models import LANGUAGE_NAMES

        if not value:
            raise serializers.ValidationError("Choose at least one language you can consult in.")
        if any(code not in LANGUAGE_NAMES for code in value):
            raise serializers.ValidationError("Unknown language.")
        return list(dict.fromkeys(value))

    def validate_availability(self, value):
        """[{day_of_week, start_time "HH:MM", end_time "HH:MM"}, ...] — optional;
        each block at least an hour (one session), no overlaps per day."""
        from datetime import datetime

        if not value:
            return []
        if len(value) > 50:
            raise serializers.ValidationError("Too many availability blocks.")
        blocks = []
        for item in value:
            try:
                day = int(item["day_of_week"])
                start = datetime.strptime(str(item["start_time"])[:5], "%H:%M").time()
                end = datetime.strptime(str(item["end_time"])[:5], "%H:%M").time()
            except (KeyError, TypeError, ValueError):
                raise serializers.ValidationError("Each availability block needs a day, a start time and an end time.")
            if not 0 <= day <= 6:
                raise serializers.ValidationError("Invalid day of the week.")
            minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
            if minutes < 60:
                raise serializers.ValidationError("Each availability block must be at least 1 hour long (one consultation).")
            blocks.append((day, start, end))
        for day in range(7):
            same_day = sorted((b for b in blocks if b[0] == day), key=lambda b: b[1])
            for prev, nxt in zip(same_day, same_day[1:]):
                if nxt[1] < prev[2]:
                    raise serializers.ValidationError("Two availability blocks on the same day overlap.")
        return blocks

    def validate_profile_photo(self, value):
        from profiles.services import ALLOWED_PROFILE_PHOTO_TYPES, MAX_PROFILE_PHOTO_BYTES

        if getattr(value, "content_type", None) not in ALLOWED_PROFILE_PHOTO_TYPES:
            raise serializers.ValidationError("Use a JPG, PNG, or WEBP image for your profile photo.")
        if value.size > MAX_PROFILE_PHOTO_BYTES:
            raise serializers.ValidationError("The profile photo must be 2 MB or smaller.")
        return value

    def validate_prc_license_number(self, value):
        value = value.strip()
        if not re.fullmatch(r"\d{7}", value):
            raise serializers.ValidationError("Enter your 7-digit PRC license number (numbers only, e.g. 0123456).")
        taken = RndProfile.objects.filter(prc_license_number=value)
        replacing = getattr(self, "_unverified_to_replace", None)
        if replacing is not None:
            taken = taken.exclude(user=replacing)
        if taken.exists():
            raise serializers.ValidationError("This PRC license number is already registered.")
        return value

    def validate_prc_license_image(self, value):
        if getattr(value, "content_type", None) not in ALLOWED_LICENSE_IMAGE_TYPES:
            raise serializers.ValidationError("Upload a JPG, PNG, or WEBP photo of your PRC license.")
        if value.size > MAX_LICENSE_IMAGE_BYTES:
            raise serializers.ValidationError("The license photo must be 5 MB or smaller.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Upload first so a failed upload never leaves a half-created account.
        try:
            license_image_id = upload_prc_license_image(validated_data["prc_license_image"])
        except LicenseImageUploadError as exc:
            raise serializers.ValidationError({"prc_license_image": [str(exc)]})

        self.remove_unverified_account()
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=User.Role.RND,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        self.record_consent(user)
        RndProfile.objects.create(
            user=user,
            prc_license_image=license_image_id,
            prc_license_number=validated_data["prc_license_number"],
            date_of_birth=validated_data["date_of_birth"],
            specialization=validated_data["specialization"],
            bio=validated_data["bio"],
            consultation_fee=validated_data["consultation_fee"],
            consultation_modes=validated_data["consultation_modes"],
            clinic_address=validated_data.get("clinic_address") if "in_person" in validated_data["consultation_modes"] else None,
            language_codes=validated_data["languages"],
            is_verified=False,
            review_status=RndProfile.ReviewStatus.PENDING,
        )
        from profiles.models import RndAvailabilitySchedule
        from profiles.services import set_rnd_languages

        set_rnd_languages(user, validated_data["languages"])
        today = timezone.now().date()
        RndAvailabilitySchedule.objects.bulk_create([
            RndAvailabilitySchedule(rnd=user, day_of_week=day, start_time=start, end_time=end, effective_from=today)
            for day, start, end in validated_data.get("availability", [])
        ])
        photo = validated_data.get("profile_photo")
        if photo is not None:
            from profiles.services import ProfilePhotoUploadError, upload_profile_photo

            try:
                user.profile_photo = upload_profile_photo(photo)
                user.save(update_fields=["profile_photo"])
            except ProfilePhotoUploadError:
                pass  # optional — they can add it after approval
        send_verification_code(user)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Deliberately does NOT raise if the email doesn't exist — the view
        # always returns the same generic success response either way, so
        # this endpoint can't be used to enumerate registered emails.
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class NutriMatchTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role/name claims to the JWT and returns the user alongside the tokens."""

    default_error_messages = {"no_active_account": "Incorrect email or password."}

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        # A deactivated account gets told why it can't sign in — but only
        # when the password is right, so the message doesn't reveal which
        # emails have accounts.
        inactive = User.objects.filter(email__iexact=(attrs.get("email") or "").strip(), is_active=False).first()
        if inactive and inactive.check_password(attrs.get("password") or ""):
            from core.support import support_email

            contact = support_email()
            raise AuthenticationFailed({
                "detail": f"Your account has been deactivated by the NutriMatch admin. To request a review, email us at {contact}.",
                "code": "account_deactivated",
                "support_email": contact,
            })
        data = super().validate(attrs)
        if self.user.email_verified_at is None:
            raise AuthenticationFailed(
                "Please verify your email before signing in. Check your inbox for the code.",
                code="email_not_verified",
            )
        if self.user.role == User.Role.RND:
            review = getattr(getattr(self.user, "rnd_profile", None), "review_status", "pending")
            if review == "rejected":
                raise AuthenticationFailed(
                    "Your RND application wasn't approved. Check your email for the reason — you can apply again with the same email.",
                    code="rnd_rejected",
                )
            if review != "approved":
                raise AuthenticationFailed(
                    "Your RND application is still under review. We'll email you as soon as it's approved.",
                    code="rnd_pending",
                )
        data["user"] = UserSerializer(self.user).data
        return data
