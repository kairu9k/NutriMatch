from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminUserDetailView,
    AdminUserListView,
    AdminUserToggleActiveView,
    AdminVerifyRndView,
    LoginView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterClientView,
    RegisterRndView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/register/client/", RegisterClientView.as_view(), name="register_client"),
    path("auth/register/rnd/", RegisterRndView.as_view(), name="register_rnd"),
    path("auth/password-reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    path("admin/users/", AdminUserListView.as_view(), name="admin_user_list"),
    path("admin/users/<int:pk>/", AdminUserDetailView.as_view(), name="admin_user_detail"),
    path("admin/users/<int:pk>/toggle-active/", AdminUserToggleActiveView.as_view(), name="admin_user_toggle_active"),
    path("admin/users/<int:pk>/verify-rnd/", AdminVerifyRndView.as_view(), name="admin_verify_rnd"),
]
