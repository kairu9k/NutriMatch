"""Admins correct a user's details (PATCH /api/admin/users/<id>/edit/):
name, email, phone, and for RNDs the PRC license number and specialization.

A reason (≥ 10 chars) is required. Only changed fields are saved; the change
is audit-logged with old → new values (`user.updated`, RA 10173) and the user
is emailed what changed — at the old address too when the email changes, so a
mistaken or malicious change doesn't go unnoticed. Admins can't edit
themselves here, and passwords are never edited (Send password reset instead)."""

import re

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.validators import validate_phone, validate_rnd_phone

from .models import User
from .permissions import IsAdmin
from .validators import validate_person_name

LABELS = {
    "first_name": "First name", "last_name": "Last name", "email": "Email", "phone": "Phone",
    "prc_license_number": "PRC license number", "specialization": "Specialization",
}


class AdminUserEditSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(max_length=254, required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    prc_license_number = serializers.CharField(max_length=20, required=False)
    specialization = serializers.CharField(max_length=100, required=False)
    reason = serializers.CharField(min_length=10, max_length=500,
                                   error_messages={"min_length": "Explain the change in at least 10 characters — it goes in the audit log."})

    def validate_first_name(self, value):
        return validate_person_name(value)

    def validate_last_name(self, value):
        return validate_person_name(value)

    def validate_email(self, value):
        value = value.strip().lower()
        user = self.context["user"]
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Another account already uses this email.")
        return value

    def validate_phone(self, value):
        if self.context["user"].role == User.Role.RND:
            if not (value or "").strip():
                raise serializers.ValidationError("RNDs must have a mobile number — enter a Philippine mobile, e.g. +63 917 123 4567.")
            return validate_rnd_phone(value)
        return validate_phone(value)

    def validate_prc_license_number(self, value):
        from profiles.models import RndProfile

        value = value.strip()
        if not re.fullmatch(r"\d{7}", value):
            raise serializers.ValidationError("Enter the 7-digit PRC license number (numbers only).")
        if RndProfile.objects.filter(prc_license_number=value).exclude(user=self.context["user"]).exists():
            raise serializers.ValidationError("Another RND already has this PRC license number.")
        return value

    def validate_specialization(self, value):
        from profiles.models import RND_SPECIALIZATIONS

        if value not in RND_SPECIALIZATIONS:
            raise serializers.ValidationError("Pick a specialization from the list.")
        return value

    def validate(self, attrs):
        user = self.context["user"]
        if user.role != User.Role.RND and ({"prc_license_number", "specialization"} & attrs.keys()):
            raise serializers.ValidationError({"detail": "PRC license and specialization only apply to RNDs."})
        attrs["reason"] = attrs["reason"].strip()
        return attrs


class AdminUserEditView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        from core.models import AuditLog

        from .serializers import UserSerializer

        user = get_object_or_404(User.objects.select_related("rnd_profile"), pk=pk)
        if user.pk == request.user.pk:
            return Response({"detail": "Edit your own details from your profile instead."}, status=status.HTTP_400_BAD_REQUEST)
        s = AdminUserEditSerializer(data=request.data, context={"user": user})
        s.is_valid(raise_exception=True)
        data = dict(s.validated_data)
        reason = data.pop("reason")

        profile = getattr(user, "rnd_profile", None)
        current = {
            "first_name": user.first_name, "last_name": user.last_name, "email": user.email, "phone": user.phone,
            "prc_license_number": getattr(profile, "prc_license_number", None),
            "specialization": getattr(profile, "specialization", None),
        }
        changes = {k: v for k, v in data.items() if (current.get(k) or None) != (v or None)}
        if not changes:
            return Response({"detail": "Nothing changed."}, status=status.HTTP_400_BAD_REQUEST)

        old_email = user.email
        with transaction.atomic():
            user_fields = [k for k in changes if k in ("first_name", "last_name", "email", "phone")]
            for k in user_fields:
                setattr(user, k, changes[k])
            if user_fields:
                user.save(update_fields=user_fields)
            profile_fields = [k for k in changes if k in ("prc_license_number", "specialization")]
            if profile_fields:
                for k in profile_fields:
                    setattr(profile, k, changes[k])
                profile.save(update_fields=profile_fields)
            AuditLog.objects.create(
                user=request.user, action="user.updated", table_name="users", record_id=user.pk,
                old_values={k: current[k] for k in changes}, new_values={**changes, "reason": reason},
            )
            transaction.on_commit(lambda: _email_user(user, changes, current, reason, old_email))
        user.refresh_from_db()
        return Response(UserSerializer(user).data)


def _email_user(user, changes, before, reason, old_email):
    from .emails import send_notice_email

    lines = [f"{LABELS[k]}: {before[k] or '—'} → {v or '—'}" for k, v in changes.items()]
    kwargs = dict(
        subject="Your NutriMatch account details were updated",
        heading="We updated your account details",
        paragraphs=["A NutriMatch admin corrected the following on your account:", *lines,
                    "If this wasn't expected, reply to this email or use Help & Support in the app."],
        highlight=f"Reason: {reason}",
        preheader="Your NutriMatch account details were updated.",
    )
    try:
        send_notice_email(user, **kwargs)
        if "email" in changes and old_email != user.email:
            # Tell the old address too.
            original = user.email
            user.email = old_email
            try:
                send_notice_email(user, **kwargs)
            finally:
                user.email = original
    except Exception:  # noqa: BLE001 — best effort
        pass
