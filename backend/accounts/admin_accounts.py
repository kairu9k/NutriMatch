"""Admin accounts and changing your own password.

POST /api/admin/admins/ {first_name, last_name, email, reason}
    An admin adds another admin. The account is created email-verified with
    no usable password; the new admin is emailed an invite to set one through
    Forgot password (a 6-digit code), so no password is ever sent by email.
    Audit row `admin.created`.

POST /api/auth/me/password/ {current_password, new_password}
    Any signed-in user changes their password: the current one must match and
    the new one passes AUTH_PASSWORD_VALIDATORS (incl. PasswordComplexityValidator).
    Audit row `password.changed`; the user is emailed a heads-up."""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .validators import validate_person_name


class AdminCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    reason = serializers.CharField(min_length=10, max_length=500,
                                   error_messages={"min_length": "Say why in at least 10 characters — it goes in the audit log."})

    def validate_first_name(self, value):
        return validate_person_name(value)

    def validate_last_name(self, value):
        return validate_person_name(value)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value


class AdminCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        from core.models import AuditLog

        from .serializers import UserSerializer

        s = AdminCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with transaction.atomic():
            admin = User.objects.create_user(
                email=d["email"], password=None, role=User.Role.ADMIN,
                first_name=d["first_name"], last_name=d["last_name"], email_verified_at=timezone.now(),
            )
            admin.set_unusable_password()
            admin.save(update_fields=["password"])
            AuditLog.objects.create(user=request.user, action="admin.created", table_name="users", record_id=admin.pk,
                                    new_values={"email": admin.email, "name": admin.full_name, "reason": d["reason"].strip()})
            transaction.on_commit(lambda: _send_invite(admin, request.user))
        return Response(UserSerializer(admin).data, status=status.HTTP_201_CREATED)


def _send_invite(admin, by):
    from .emails import send_notice_email

    try:
        send_notice_email(
            admin,
            subject="You've been added as a NutriMatch admin",
            heading="Welcome to the NutriMatch admin team",
            paragraphs=[
                f"{by.full_name} added you as an administrator of NutriMatch.",
                "To start, set your password: open the link below, choose Forgot password, enter this email address "
                "and type the 6-digit code we send you. Then sign in on the admin sign-in page.",
            ],
            highlight=f"Your admin sign-in email: {admin.email}",
            button_label="Set your password",
            button_url=f"{settings.FRONTEND_URL}/forgot-password",
            preheader="Set your password to start using the NutriMatch admin portal.",
        )
    except Exception:  # noqa: BLE001 — best effort; they can still use Forgot password
        pass


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(trim_whitespace=False, max_length=128)

    def validate(self, attrs):
        user = self.context["user"]
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "That's not your current password."})
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError({"new_password": "Choose a password different from your current one."})
        try:
            validate_password(attrs["new_password"], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        return attrs


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"  # same budget as the reset-code check

    def post(self, request):
        from core.models import AuditLog

        from .emails import send_notice_email

        s = ChangePasswordSerializer(data=request.data, context={"user": request.user})
        s.is_valid(raise_exception=True)
        user = request.user
        user.set_password(s.validated_data["new_password"])
        user.save(update_fields=["password"])
        AuditLog.objects.create(user=user, action="password.changed", table_name="users", record_id=user.pk)
        try:
            send_notice_email(
                user, subject="Your NutriMatch password was changed", heading="Your password was changed",
                paragraphs=["The password for your NutriMatch account was just changed.",
                            "If this wasn't you, reset it right away with Forgot password and contact us."],
                preheader="Your NutriMatch password was changed.",
            )
        except Exception:  # noqa: BLE001
            pass
        return Response({"detail": "Password changed."})
