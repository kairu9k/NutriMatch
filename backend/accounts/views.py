from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdmin, IsClient
from .serializers import (
    EMAIL_TAKEN_MESSAGE,
    AdminClientListSerializer,
    AdminRndListSerializer,
    MeUpdateSerializer,
    NutriMatchTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterClientSerializer,
    RegisterRndSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    email_blocks_registration,
)
from .services import (
    InvalidResetCodeError,
    InvalidVerificationCodeError,
    consume_reset_code,
    request_password_reset,
    send_verification_code,
    verify_email_code,
)


class LoginView(TokenObtainPairView):
    serializer_class = NutriMatchTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RegisterClientView(generics.CreateAPIView):
    serializer_class = RegisterClientSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class RegisterEmailCheckView(APIView):
    """POST {email} → {available}. Lets the sign-up form stop on the details
    step ("An account with this email already exists.") instead of only
    finding out at the final submit. Same rule as registration itself, so an
    unfinished signup or a rejected RND application still counts as free."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register_email_check"

    def post(self, request):
        email = str(request.data.get("email") or "").strip()
        if not email:
            return Response({"email": ["Enter an email address."]}, status=status.HTTP_400_BAD_REQUEST)
        existing = User.objects.filter(email__iexact=email).first()
        if email_blocks_registration(existing):
            return Response({"available": False, "detail": EMAIL_TAKEN_MESSAGE})
        return Response({"available": True})


class RegisterRndView(generics.CreateAPIView):
    serializer_class = RegisterRndSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verify_email"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.filter(email__iexact=data["email"], deleted_at__isnull=True).first()
        if user is None:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verify_email_code(user, data["code"])
        except InvalidVerificationCodeError:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Email verified. You can now sign in."})


class ResendVerificationView(APIView):
    """Always returns a generic success response, whether or not the email
    is registered or already verified — same anti-enumeration reasoning as
    PasswordResetRequestView."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend_verification"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            deleted_at__isnull=True,
            email_verified_at__isnull=True,
        ).first()
        if user:
            send_verification_code(user)

        return Response({"detail": "If that email needs verification, a new code has been sent."})


class PasswordResetRequestView(APIView):
    """Always returns a generic success response, whether or not the email
    is registered — otherwise this endpoint could be used to enumerate
    accounts by email address."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_request"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email__iexact=serializer.validated_data["email"], deleted_at__isnull=True).first()
        if user:
            request_password_reset(user)

        return Response({"detail": "If that email is registered, a reset code has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.filter(email__iexact=data["email"], deleted_at__isnull=True).first()
        if user is None:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            consume_reset_code(user, data["code"], data["new_password"])
        except InvalidResetCodeError:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Password reset successfully. You can now sign in."})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class MePhotoView(APIView):
    """POST (multipart `photo`) sets the signed-in user's profile photo;
    DELETE removes it. The previous photo is deleted from Cloudinary."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        from profiles.services import (
            ALLOWED_PROFILE_PHOTO_TYPES, MAX_PROFILE_PHOTO_BYTES, ProfilePhotoUploadError,
            destroy_profile_photo, upload_profile_photo,
        )

        photo = request.FILES.get("photo")
        if photo is None:
            return Response({"photo": ["Choose a photo to upload."]}, status=status.HTTP_400_BAD_REQUEST)
        if photo.content_type not in ALLOWED_PROFILE_PHOTO_TYPES:
            return Response({"photo": ["Use a JPG, PNG, or WEBP image."]}, status=status.HTTP_400_BAD_REQUEST)
        if photo.size > MAX_PROFILE_PHOTO_BYTES:
            return Response({"photo": ["The photo must be 2 MB or smaller."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = upload_profile_photo(photo)
        except ProfilePhotoUploadError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        old = request.user.profile_photo
        request.user.profile_photo = url
        request.user.save(update_fields=["profile_photo", "updated_at"])
        if old and old != url:
            destroy_profile_photo(old)
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        from profiles.services import destroy_profile_photo

        old = request.user.profile_photo
        if old:
            request.user.profile_photo = None
            request.user.save(update_fields=["profile_photo", "updated_at"])
            destroy_profile_photo(old)
        return Response(UserSerializer(request.user).data)


class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = User.objects.all().order_by("-created_at")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs


class AdminUserDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError

        from core.models import AuditLog

        if instance.pk == self.request.user.pk:
            raise ValidationError({"detail": "You can't remove your own account."})
        instance.deleted_at = timezone.now()
        instance.is_active = False
        instance.save(update_fields=["deleted_at", "is_active"])
        AuditLog.objects.create(user=self.request.user, action="user.removed", table_name="users", record_id=instance.pk)


class AdminUserToggleActiveView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        from core.models import AuditLog

        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            return Response({"detail": "You can't deactivate your own account."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        AuditLog.objects.create(user=request.user, action="user.reactivated" if user.is_active else "user.deactivated",
                                table_name="users", record_id=user.pk)
        return Response(UserSerializer(user).data)


class AdminVerifyRndView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        from profiles.models import RndProfile

        from core.models import AuditLog

        from .emails import send_notice_email

        user = get_object_or_404(User, pk=pk, role=User.Role.RND)
        profile = get_object_or_404(RndProfile, user=user)
        if user.email_verified_at is None:
            return Response({"detail": "This applicant hasn't verified their email yet."}, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        profile.is_verified = True
        profile.verified_at = now
        profile.review_status = RndProfile.ReviewStatus.APPROVED
        profile.rejection_reason = None
        profile.reviewed_at = now
        profile.save(update_fields=["is_verified", "verified_at", "review_status", "rejection_reason", "reviewed_at"])
        if user.onboarding_completed_at is None:
            user.onboarding_completed_at = now  # the application held everything onboarding needs
            user.save(update_fields=["onboarding_completed_at"])
        AuditLog.objects.create(user=request.user, action="rnd.approved", table_name="rnd_profiles", record_id=profile.id, new_values={"review_status": "approved"})
        send_notice_email(
            user,
            subject="Your NutriMatch RND account is approved",
            heading="You're approved! 🎉",
            paragraphs=[
                "Good news — our team has reviewed your PRC license and profile, and your NutriMatch RND account is now active.",
                "You can sign in now. Add your weekly hours in Profile Settings — then clients can find your profile, book consultations within those hours, and pay before each session.",
            ],
            button_label="Sign in to NutriMatch",
            button_url=f"{settings.FRONTEND_URL}/login",
            preheader="Your RND account is active — you can sign in now.",
        )
        return Response(UserSerializer(user).data)


class AdminRejectRndView(APIView):
    """Admin declines an RND application, with a reason that's emailed to
    the applicant. They can register again with the same email."""

    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        from profiles.models import RndProfile

        from core.models import AuditLog

        from .emails import send_notice_email

        user = get_object_or_404(User, pk=pk, role=User.Role.RND)
        profile = get_object_or_404(RndProfile, user=user)
        reason = (request.data.get("reason") or "").strip()
        if len(reason) < 10:
            return Response({"reason": ["Explain why in at least 10 characters — the applicant will see this."]}, status=status.HTTP_400_BAD_REQUEST)
        if len(reason) > 1000:
            return Response({"reason": ["Keep the reason under 1,000 characters."]}, status=status.HTTP_400_BAD_REQUEST)
        if profile.review_status == RndProfile.ReviewStatus.APPROVED:
            return Response({"detail": "This RND is already approved. Deactivate the account instead."}, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        profile.is_verified = False
        profile.review_status = RndProfile.ReviewStatus.REJECTED
        profile.rejection_reason = reason
        profile.reviewed_at = now
        profile.save(update_fields=["is_verified", "review_status", "rejection_reason", "reviewed_at"])
        AuditLog.objects.create(user=request.user, action="rnd.rejected", table_name="rnd_profiles", record_id=profile.id, new_values={"review_status": "rejected", "reason": reason})
        send_notice_email(
            user,
            subject="Update on your NutriMatch RND application",
            heading="We couldn't approve your application yet",
            paragraphs=[
                "Thank you for applying to NutriMatch. Our team reviewed your PRC license and profile, but we can't approve your account at this time.",
                "You're welcome to apply again with the same email once the issue below is fixed.",
            ],
            highlight=f"Reason: {reason}",
            button_label="Apply again",
            button_url=f"{settings.FRONTEND_URL}/register",
            preheader="Your application wasn't approved — here's why, and how to apply again.",
        )
        return Response({"id": user.id, "review_status": profile.review_status})


class OnboardingStatusView(APIView):
    """What the signed-in user still has to do before using the app."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .onboarding import onboarding_status

        return Response(onboarding_status(request.user))


class OnboardingCompleteView(APIView):
    """Client finishes onboarding — only once the required steps are done."""

    permission_classes = [IsClient]

    def post(self, request):
        from .onboarding import onboarding_status

        state = onboarding_status(request.user)
        pending = [s["label"] for s in state["steps"] if s["required"] and not s["done"]]
        if pending:
            return Response({"detail": "Finish these first: " + "; ".join(pending) + "."}, status=status.HTTP_400_BAD_REQUEST)
        if request.user.onboarding_completed_at is None:
            request.user.onboarding_completed_at = timezone.now()
            request.user.welcome_seen_at = request.user.welcome_seen_at or timezone.now()
            request.user.save(update_fields=["onboarding_completed_at", "welcome_seen_at"])
        return Response(onboarding_status(request.user))


class WelcomeSeenView(APIView):
    """The signed-in user closed the one-time welcome message."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.welcome_seen_at is None:
            request.user.welcome_seen_at = timezone.now()
            request.user.save(update_fields=["welcome_seen_at"])
        return Response(UserSerializer(request.user).data)


class AdminRndListView(generics.ListAPIView):
    """All RNDs (pending + verified + deactivated) for RndVerification.vue
    — one page covering the whole lifecycle, filtered client-side by the
    frontend's status tabs."""

    serializer_class = AdminRndListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        from billing.models import Invoice
        from scheduling.models import Appointment, Review, RndClientRelationship

        relationships_qs = RndClientRelationship.objects.prefetch_related(
            Prefetch(
                "invoices",
                queryset=Invoice.objects.filter(status=Invoice.Status.PAID),
                to_attr="_prefetched_paid_invoices",
            ),
            Prefetch(
                "appointments",
                queryset=Appointment.objects.filter(status=Appointment.Status.COMPLETED),
                to_attr="_prefetched_completed_appointments",
            ),
        )
        return User.objects.filter(role=User.Role.RND).select_related("rnd_profile").prefetch_related(
            Prefetch("client_relationships", queryset=relationships_qs, to_attr="_prefetched_relationships"),
            Prefetch("reviews_received", queryset=Review.objects.filter(is_public=True), to_attr="_prefetched_reviews"),
        ).order_by("-rnd_profile__created_at")


class AdminClientListView(generics.ListAPIView):
    """All clients for ClientManagement.vue. condition/consultations/
    matched-RND all come from prefetches, same one-query-per-relation
    pattern as scheduling.RndPatientListSerializer."""

    serializer_class = AdminClientListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        from scheduling.models import Appointment, RndClientRelationship

        return User.objects.filter(role=User.Role.CLIENT).select_related("health_profile").prefetch_related(
            Prefetch(
                "rnd_relationships",
                queryset=RndClientRelationship.objects.select_related("rnd").prefetch_related(
                    Prefetch("appointments", queryset=Appointment.objects.all(), to_attr="_prefetched_appointments"),
                ),
                to_attr="_prefetched_relationships",
            ),
        ).order_by("-created_at")





# ------------------------------------------------------------ admin users
class AdminUserOverviewView(APIView):
    """Everything an admin can see about one user (admins see everything —
    user's decision, 2026-10-10 — except passwords, which are hashed).
    Opening a client's record is audit-logged because it shows health data."""

    permission_classes = [IsAdmin]

    def get(self, request, pk):
        from .admin_overview import user_overview

        user = get_object_or_404(User, pk=pk)
        return Response(user_overview(user, viewer=request.user, request=request))


class AdminDeactivateUserView(APIView):
    """Deactivate with a reason: the user can't sign in or use the API, is
    emailed the reason, and the action is audit-logged."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from core.models import AuditLog
        from core.support import support_email

        from .emails import send_notice_email

        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            return Response({"detail": "You can't deactivate your own account."}, status=status.HTTP_400_BAD_REQUEST)
        reason = (request.data.get("reason") or "").strip()
        if len(reason) < 10:
            return Response({"reason": ["Explain why in at least 10 characters — the user will see this."]}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "This account is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = False
        user.save(update_fields=["is_active"])
        AuditLog.objects.create(user=request.user, action="user.deactivated", table_name="users", record_id=user.pk,
                                new_values={"reason": reason[:1000]})
        try:
            send_notice_email(
                user,
                subject="Your NutriMatch account has been deactivated",
                heading="Your account has been deactivated",
                paragraphs=[
                    "Our team has deactivated your NutriMatch account, so you can't sign in for now.",
                    f"If you think this is a mistake, email us at {support_email()} to request a review, and we'll look into it.",
                ],
                highlight=f"Reason: {reason[:1000]}",
                preheader="Your NutriMatch account has been deactivated.",
            )
        except Exception:
            pass
        return Response(UserSerializer(user).data)


class AdminReactivateUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from core.models import AuditLog

        from .emails import send_notice_email

        user = get_object_or_404(User, pk=pk)
        if user.is_active:
            return Response({"detail": "This account is already active."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=["is_active"])
        AuditLog.objects.create(user=request.user, action="user.reactivated", table_name="users", record_id=user.pk)
        try:
            send_notice_email(
                user,
                subject="Your NutriMatch account is active again",
                heading="Welcome back! Your account is active again",
                paragraphs=["Your NutriMatch account has been reactivated — you can sign in again."],
                button_label="Sign in to NutriMatch",
                button_url=f"{settings.FRONTEND_URL}/login",
                preheader="You can sign in to NutriMatch again.",
            )
        except Exception:
            pass
        return Response(UserSerializer(user).data)


class AdminSendPasswordResetView(APIView):
    """Admins can't see passwords (they're hashed) — this emails the user a
    reset code instead."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from core.models import AuditLog

        user = get_object_or_404(User, pk=pk)
        if not user.is_active:
            return Response({"detail": "Reactivate the account first."}, status=status.HTTP_400_BAD_REQUEST)
        request_password_reset(user)
        AuditLog.objects.create(user=request.user, action="user.password_reset_sent", table_name="users", record_id=user.pk)
        return Response({"detail": f"A password reset code was emailed to {user.email}."})
