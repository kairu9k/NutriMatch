from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .admin_edit import AdminUserEditView

from .views import (
    AdminClientListView,
    AdminRndListView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserToggleActiveView,
    AdminVerifyRndView,
    LoginView,
    MePhotoView,
    OnboardingCompleteView,
    OnboardingStatusView,
    WelcomeSeenView,
    AdminRejectRndView,
    AdminUserOverviewView,
    AdminDeactivateUserView,
    AdminReactivateUserView,
    AdminSendPasswordResetView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterClientView,
    RegisterRndView,
    ResendVerificationView,
    VerifyEmailView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/me/photo/", MePhotoView.as_view(), name="me_photo"),
    path("auth/me/onboarding/", OnboardingStatusView.as_view(), name="onboarding_status"),
    path("auth/me/onboarding/complete/", OnboardingCompleteView.as_view(), name="onboarding_complete"),
    path("auth/me/welcome-seen/", WelcomeSeenView.as_view(), name="welcome_seen"),
    path("auth/register/client/", RegisterClientView.as_view(), name="register_client"),
    path("auth/register/rnd/", RegisterRndView.as_view(), name="register_rnd"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("auth/verify-email/resend/", ResendVerificationView.as_view(), name="resend_verification"),
    path("auth/password-reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    path("admin/users/", AdminUserListView.as_view(), name="admin_user_list"),
    path("admin/users/<int:pk>/", AdminUserDetailView.as_view(), name="admin_user_detail"),
    path("admin/users/<int:pk>/toggle-active/", AdminUserToggleActiveView.as_view(), name="admin_user_toggle_active"),
    path("admin/users/<int:pk>/verify-rnd/", AdminVerifyRndView.as_view(), name="admin_verify_rnd"),
    path("admin/users/<int:pk>/reject-rnd/", AdminRejectRndView.as_view(), name="admin_reject_rnd"),
    path("admin/users/<int:pk>/overview/", AdminUserOverviewView.as_view(), name="admin_user_overview"),
    path("admin/users/<int:pk>/edit/", AdminUserEditView.as_view(), name="admin_user_edit"),
    path("admin/users/<int:pk>/deactivate/", AdminDeactivateUserView.as_view(), name="admin_user_deactivate"),
    path("admin/users/<int:pk>/reactivate/", AdminReactivateUserView.as_view(), name="admin_user_reactivate"),
    path("admin/users/<int:pk>/send-password-reset/", AdminSendPasswordResetView.as_view(), name="admin_user_password_reset"),
    path("admin/rnds/", AdminRndListView.as_view(), name="admin_rnd_list"),
    path("admin/clients/", AdminClientListView.as_view(), name="admin_client_list"),
]
