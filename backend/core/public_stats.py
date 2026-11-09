"""The landing page's real numbers: two totals, nothing about any person.
Public (no sign-in), so it's cached briefly and never touches a token."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

CACHE_KEY = "public_landing_stats"
CACHE_SECONDS = 300


def landing_stats():
    """Verified RNDs: approved accounts that are still active. Clients served:
    people with at least one completed consultation (registering isn't being served)."""
    from profiles.models import RndProfile
    from scheduling.models import Appointment

    return {
        "verified_rnds": RndProfile.objects.filter(is_verified=True, user__is_active=True).count(),
        "clients_served": get_user_model().objects.filter(
            pk__in=Appointment.objects.filter(status=Appointment.Status.COMPLETED).values("relationship__client")
        ).count(),
    }


class PublicLandingStatsView(APIView):
    authentication_classes = []  # an expired token in the browser mustn't turn this into a 401
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(cache.get_or_set(CACHE_KEY, landing_stats, CACHE_SECONDS))
