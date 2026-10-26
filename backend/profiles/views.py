from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import Review, RndClientRelationship

from .models import ClientProfile, RndAvailabilitySchedule, RndProfile
from .serializers import (
    ClientProfileSerializer,
    ClientProfileUpdateSerializer,
    PublicReviewSerializer,
    MyRndProfileSerializer,
    RndAvailabilityScheduleSerializer,
    RndProfileSerializer,
    RndProfileUpdateSerializer,
)


class RndSearchOptionsView(APIView):
    """Specializations / languages / formats for the Find an RND filters."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .public import search_options

        return Response(search_options())


class RndSearchView(generics.ListAPIView):
    """Client-facing RND search: filter by specialty, language, availability.

    Only verified, active-for-new-clients RNDs are surfaced — unverified RNDs
    (pending PRC review) must not appear to clients.
    """

    permission_classes = [IsClient]

    def get_serializer_class(self):
        from .public import PublicRndProfileSerializer

        return PublicRndProfileSerializer

    def get_queryset(self):
        from .services import bookable_rnd_profiles

        # Approved + fee + bio + availability (bookable_rnd_profiles), and
        # taking new clients.
        qs = bookable_rnd_profiles().filter(available_for_new_clients=True).select_related("user")

        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialization__icontains=specialty)

        language = self.request.query_params.get("language")
        if language:
            qs = qs.filter(user__languages__language_code=language)

        name = (self.request.query_params.get("search") or "").strip()
        if name:
            from django.db.models import Q

            for part in name.split():
                qs = qs.filter(Q(user__first_name__icontains=part) | Q(user__last_name__icontains=part))

        max_fee = self.request.query_params.get("max_fee")
        if max_fee:
            try:
                qs = qs.filter(consultation_fee__lte=float(max_fee))
            except ValueError:
                pass

        qs = qs.distinct().prefetch_related("user__languages")

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

    permission_classes = [permissions.IsAuthenticated]
    queryset = RndProfile.objects.select_related("user")

    def get_serializer_class(self):
        from .public import PublicRndDetailSerializer

        return PublicRndDetailSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "slot_count": 6}
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
        return Response(MyRndProfileSerializer(profile).data)

    def patch(self, request):
        profile, _ = RndProfile.objects.get_or_create(user=request.user)
        serializer = RndProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MyRndProfileSerializer(profile).data)


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
    """Edit or remove one weekly block — refused while an upcoming booking sits
    in the hours being taken away (profiles/availability_guard.py)."""

    serializer_class = RndAvailabilityScheduleSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return RndAvailabilitySchedule.objects.filter(rnd=self.request.user)

    def update(self, request, *args, **kwargs):
        from .availability_guard import bookings_left_outside, refusal

        block = self.get_object()
        serializer = self.get_serializer(block, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        new = {f: serializer.validated_data.get(f, getattr(block, f)) for f in
               ("day_of_week", "start_time", "end_time", "effective_from", "effective_to")}
        if serializer.validated_data.get("is_available", block.is_available):
            blocked = bookings_left_outside(request.user, remove_id=block.id, replacement=new)
        else:
            blocked = bookings_left_outside(request.user, remove_id=block.id)
        if blocked:
            return Response(refusal(blocked), status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        from .availability_guard import bookings_left_outside, refusal

        block = self.get_object()
        blocked = bookings_left_outside(request.user, remove_id=block.id)
        if blocked:
            return Response(refusal(blocked), status=status.HTTP_400_BAD_REQUEST)
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
