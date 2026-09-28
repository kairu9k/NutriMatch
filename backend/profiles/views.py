from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import Review, RndClientRelationship

from .models import ClientProfile, RndAvailabilitySchedule, RndProfile
from .serializers import (
    ClientProfileSerializer,
    ClientProfileUpdateSerializer,
    PublicReviewSerializer,
    RndAvailabilityScheduleSerializer,
    RndProfileSerializer,
    RndProfileUpdateSerializer,
)


class RndSearchView(generics.ListAPIView):
    """Client-facing RND search: filter by specialty, language, availability.

    Only verified, active-for-new-clients RNDs are surfaced — unverified RNDs
    (pending PRC review) must not appear to clients.
    """

    serializer_class = RndProfileSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        qs = RndProfile.objects.filter(
            is_verified=True, available_for_new_clients=True
        ).select_related("user")

        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialization__icontains=specialty)

        language = self.request.query_params.get("language")
        if language:
            qs = qs.filter(user__languages__language_code=language)

        qs = qs.distinct()

        # JSONField list containment isn't supported on SQLite (dev DB), so
        # this filter runs in Python — the verified-RND list is small.
        mode = self.request.query_params.get("mode")
        if mode:
            return [p for p in qs if mode in (p.consultation_modes or [])]
        return qs


class RndDetailView(generics.RetrieveAPIView):
    """average_rating/review_count come from RndProfileSerializer itself
    now, so this needs no special-case aggregate logic — same as the list
    view (RndSearchView)."""

    serializer_class = RndProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = RndProfile.objects.select_related("user")
    lookup_url_kwarg = "rnd_id"
    lookup_field = "user_id"


class RndPublicReviewsView(generics.ListAPIView):
    """Public reviews for an RND's profile page — visible to any client."""

    serializer_class = PublicReviewSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return Review.objects.filter(
            rnd_id=self.kwargs["rnd_id"], is_public=True
        ).select_related("client").order_by("-created_at")


class MyRndProfileView(APIView):
    """RND managing their own profile."""

    permission_classes = [IsRnd]

    def get(self, request):
        profile, _ = RndProfile.objects.get_or_create(user=request.user)
        return Response(RndProfileSerializer(profile).data)

    def patch(self, request):
        profile, _ = RndProfile.objects.get_or_create(user=request.user)
        serializer = RndProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RndProfileSerializer(profile).data)


class MyClientProfileView(APIView):
    """Client managing their own profile."""

    permission_classes = [IsClient]

    def get(self, request):
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)
        return Response(ClientProfileSerializer(profile).data)

    def patch(self, request):
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)
        serializer = ClientProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ClientProfileSerializer(profile).data)


class RndAvailabilityListCreateView(generics.ListCreateAPIView):
    """RND managing their own weekly availability slots. Only the recurring
    day_of_week/start_time/end_time shape is supported — there's no
    per-date blocking concept in this model (or the DBML schema), so
    one-off blocked days are deliberately not part of this API."""

    serializer_class = RndAvailabilityScheduleSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return RndAvailabilitySchedule.objects.filter(rnd=self.request.user).order_by("day_of_week", "start_time")

    def perform_create(self, serializer):
        serializer.save(rnd=self.request.user)


class RndAvailabilityDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = RndAvailabilityScheduleSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return RndAvailabilitySchedule.objects.filter(rnd=self.request.user)


class RndPublicAvailabilityView(generics.ListAPIView):
    """Public weekly availability for an RND's profile page — visible to
    any client, read-only."""

    serializer_class = RndAvailabilityScheduleSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return RndAvailabilitySchedule.objects.filter(
            rnd_id=self.kwargs["rnd_id"], is_available=True
        ).order_by("day_of_week", "start_time")


class RndClientProfileView(APIView):
    """RND viewing one of their own clients' profile/health data —
    scoped to an existing relationship, never open client lookup."""

    permission_classes = [IsRnd]

    def get(self, request, relationship_id):
        relationship = get_object_or_404(
            RndClientRelationship.objects.select_related("client"),
            pk=relationship_id, rnd=request.user,
        )
        profile, _ = ClientProfile.objects.get_or_create(user=relationship.client)
        return Response(ClientProfileSerializer(profile).data)
