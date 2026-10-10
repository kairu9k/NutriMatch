from rest_framework.permissions import BasePermission

from .models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)


class IsRnd(BasePermission):
    """An RND whose application has been approved. Unapproved RNDs can't sign
    in at all; this also blocks any token issued before that rule existed."""

    message = "Your RND application hasn't been approved yet."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.role == User.Role.RND):
            return False
        profile = getattr(user, "rnd_profile", None)
        return bool(profile and profile.is_verified)


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.CLIENT)
