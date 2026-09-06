import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone

from .models import PasswordResetCode

CODE_LENGTH = 6
CODE_TTL_MINUTES = 15


def request_password_reset(user):
    """Generates a fresh 6-digit code for the user and emails it. Any
    earlier unused codes for this user are left alone — they just expire
    naturally or get consumed/invalidated on next use."""

    code = "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))
    reset = PasswordResetCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=CODE_TTL_MINUTES),
    )
    send_mail(
        subject="Your NutriMatch password reset code",
        message=(
            f"Hi {user.first_name},\n\n"
            f"Your password reset code is: {code}\n\n"
            f"This code expires in {CODE_TTL_MINUTES} minutes. "
            "If you didn't request a password reset, you can ignore this email.\n\n"
            "— NutriMatch"
        ),
        from_email=None,
        recipient_list=[user.email],
    )
    return reset


class InvalidResetCodeError(Exception):
    pass


def verify_reset_code(user, code):
    """Returns the matching unused, unexpired PasswordResetCode or raises
    InvalidResetCodeError. Doesn't mark it used — that happens atomically
    with the password change in consume_reset_code, so a verify-only check
    (if ever needed) can't burn a code the user hasn't actually used yet."""

    reset = PasswordResetCode.objects.filter(
        user=user, code=code, used_at__isnull=True, expires_at__gt=timezone.now()
    ).order_by("-created_at").first()
    if reset is None:
        raise InvalidResetCodeError("Invalid or expired code.")
    return reset


def consume_reset_code(user, code, new_password):
    reset = verify_reset_code(user, code)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    reset.used_at = timezone.now()
    reset.save(update_fields=["used_at"])
