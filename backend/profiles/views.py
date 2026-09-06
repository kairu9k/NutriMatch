from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import Review, RndClientRelationship

from .models import ClientProfile, RndProfile
from .serializers import (
    ClientProfileSerializer,
    ClientProfileUpdateSerializer,
    PublicReviewSerializer,
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

        return qs.distinct()


class RndDetailView(generics.RetrieveAPIView):
    serializer_class = RndProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = RndProfile.objects.select_related("user")
    lookup_url_kwarg = "rnd_id"
    lookup_field = "user_id"

    def get_object(self):
        obj = super().get_object()
        agg = Review.objects.filter(rnd_id=obj.user_id, is_public=True).aggregate(
            avg_rating=Avg("rating"), review_count=Count("id")
        )
        self._avg_rating = agg["avg_rating"]
        self._review_count = agg["review_count"]
        return obj

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response.data["average_rating"] = self._avg_rating
        response.data["review_count"] = self._review_count
        return response


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
