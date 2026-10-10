import secrets
from datetime import timedelta

from django.utils import timezone

from .emails import send_code_email
from .models import EmailVerificationCode, PasswordResetCode

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
    send_code_email(
        user,
        subject="Your NutriMatch password reset code",
        heading="Reset your password",
        intro="We received a request to reset the password for your NutriMatch account. Enter this code to choose a new password.",
        code=code,
        ttl_minutes=CODE_TTL_MINUTES,
        after_code="For your security, the code works only once.",
        safety_note="Didn't ask to reset your password? You can ignore this email — your password won't change. Never share this code with anyone, including NutriMatch staff.",
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


def send_verification_code(user):
    """Generates a fresh 6-digit code for the user and emails it. Any
    earlier unused codes for this user are left alone — same pattern as
    request_password_reset."""

    code = "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))
    verification = EmailVerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=CODE_TTL_MINUTES),
    )
    send_code_email(
        user,
        subject="Verify your NutriMatch email address",
        heading="Confirm your email address",
        intro="Welcome to NutriMatch! Enter this code on the sign-up page to confirm your email address and activate your account.",
        code=code,
        ttl_minutes=CODE_TTL_MINUTES,
        after_code="Once it's confirmed, you can sign in and get started.",
        safety_note="Didn't create a NutriMatch account? You can safely ignore this email. Never share this code with anyone.",
    )
    return verification


class InvalidVerificationCodeError(Exception):
    pass


def verify_email_code(user, code):
    """Marks the user's email verified if the code matches an unused,
    unexpired EmailVerificationCode. Raises InvalidVerificationCodeError
    otherwise. Idempotent-ish: if the user is already verified this still
    requires a valid code — callers should check email_verified_at first
    if they want to short-circuit that case."""

    verification = EmailVerificationCode.objects.filter(
        user=user, code=code, used_at__isnull=True, expires_at__gt=timezone.now()
    ).order_by("-created_at").first()
    if verification is None:
        raise InvalidVerificationCodeError("Invalid or expired code.")

    verification.used_at = timezone.now()
    verification.save(update_fields=["used_at"])
    user.email_verified_at = timezone.now()
    user.save(update_fields=["email_verified_at"])
