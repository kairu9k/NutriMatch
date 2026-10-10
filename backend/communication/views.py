from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import RndClientRelationship

from .models import Message, NotificationLog, Resource, ResourceShare
from .serializers import MessageSerializer, NotificationDetailSerializer, NotificationLogSerializer, ResourceSerializer
from .services import CloudinaryResourceUploadService, ResourceUploadError, notify


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_relationship(self):
        user = self.request.user
        return get_object_or_404(
            RndClientRelationship.objects.filter(Q(rnd=user) | Q(client=user)),
            id=self.kwargs["relationship_id"],
        )

    def get_queryset(self):
        relationship = self.get_relationship()
        return Message.objects.filter(
            relationship=relationship, deleted_at__isnull=True
        ).select_related("sender").order_by("created_at")

    def create(self, request, *args, **kwargs):
        relationship = self.get_relationship()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(relationship=relationship, sender=request.user)

        recipient = relationship.client if request.user.id == relationship.rnd_id else relationship.rnd
        notify(
            recipient=recipient,
            notifiable_type="message",
            notifiable_id=message.id,
            subject="New message",
            content=f"{request.user.full_name}: {message.message[:200]}",
        )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        message.deleted_at = timezone.now()
        message.save(update_fields=["deleted_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "client":
            from .reminders import run_for_client_throttled

            run_for_client_throttled(self.request.user)
        return NotificationLog.objects.filter(
            recipient=self.request.user, channel=NotificationLog.Channel.IN_APP
        ).order_by("-created_at")


class NotificationDetailView(generics.RetrieveAPIView):
    """One of the user's own notifications with a summary of what it's
    about — the notification detail overlay."""

    serializer_class = NotificationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(recipient=self.request.user, channel=NotificationLog.Channel.IN_APP)


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(
            NotificationLog.objects.filter(recipient=request.user), pk=pk
        )
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationLogSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        NotificationLog.objects.filter(
            recipient=request.user, channel=NotificationLog.Channel.IN_APP, is_read=False
        ).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _rnd_resources(user):
    """The RND's own resources, each annotated with how many active clients
    it's currently shared with."""
    return Resource.objects.filter(uploaded_by=user).annotate(
        _shared_count=Count(
            "shares", filter=Q(shares__relationship__status=RndClientRelationship.Status.ACTIVE)
        )
    )


class RndResourceListCreateView(generics.ListCreateAPIView):
    """RND's own uploaded resources. 'link' type stores a URL directly;
    every other type uploads its file to Cloudinary (see
    CloudinaryResourceUploadService) and stores the resulting secure URL
    as file_path. Uploading shares it with nobody — see RndResourceShareView."""

    serializer_class = ResourceSerializer
    permission_classes = [IsRnd]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return _rnd_resources(self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        file = serializer.validated_data.pop("file", None)
        file_path = None
        if file is not None:
            try:
                file_path = CloudinaryResourceUploadService().upload(file)
            except ResourceUploadError as exc:
                raise serializers.ValidationError({"file": [str(exc)]})
        # A multipart form without `is_active` reads as False in DRF (HTML
        # checkbox rule), which silently hid every new upload. New resources
        # start active unless the request explicitly says otherwise — who
        # sees them is decided by sharing, not by this flag.
        is_active = serializer.validated_data.get("is_active", True) if "is_active" in self.request.data else True
        serializer.save(uploaded_by=self.request.user, file_path=file_path, is_active=is_active)


class RndResourceUpdateView(generics.UpdateAPIView):
    """RND toggling their own resource active/inactive, or editing it."""

    serializer_class = ResourceSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return _rnd_resources(self.request.user)


class RndResourceShareView(APIView):
    """Who an RND's resource is shared with, and sharing it with more.

    GET  → every active (confirmed) client of this RND, marked shared or not.
    POST {relationship_ids: [...]} → share with those clients (each must be
         one of this RND's active relationships); newly added clients get a
         notification, ones that already had it are left alone.
    """

    permission_classes = [IsRnd]

    def _resource(self, request, pk):
        return get_object_or_404(Resource, pk=pk, uploaded_by=request.user)

    def _rows(self, request, resource):
        shared = {s.relationship_id: s.shared_at for s in resource.shares.all()}
        relationships = (
            RndClientRelationship.objects.filter(rnd=request.user, status=RndClientRelationship.Status.ACTIVE)
            .select_related("client")
            .order_by("client__first_name", "client__last_name")
        )
        return [
            {
                "relationship_id": rel.id,
                "client": {
                    "id": rel.client.id,
                    "full_name": rel.client.full_name,
                    "email": rel.client.email,
                    "profile_photo": rel.client.profile_photo,
                },
                "shared": rel.id in shared,
                "shared_at": shared.get(rel.id),
            }
            for rel in relationships
        ]

    def get(self, request, pk):
        resource = self._resource(request, pk)
        return Response(self._rows(request, resource))

    def post(self, request, pk):
        resource = self._resource(request, pk)
        ids = request.data.get("relationship_ids")
        if not isinstance(ids, list) or not ids or not all(type(i) is int for i in ids):
            return Response(
                {"relationship_ids": ["Choose at least one client."]}, status=status.HTTP_400_BAD_REQUEST
            )
        relationships = list(
            RndClientRelationship.objects.filter(
                rnd=request.user, status=RndClientRelationship.Status.ACTIVE, id__in=set(ids)
            ).select_related("client")
        )
        if len(relationships) != len(set(ids)):
            return Response(
                {"relationship_ids": ["You can only share resources with your own confirmed clients."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        already = set(resource.shares.values_list("relationship_id", flat=True))
        for rel in relationships:
            if rel.id in already:
                continue
            ResourceShare.objects.create(resource=resource, relationship=rel)
            notify(
                recipient=rel.client,
                notifiable_type="resource",
                notifiable_id=resource.id,
                subject="New resource shared",
                content=f"{request.user.full_name} shared \"{resource.title}\" with you.",
            )
        return Response(self._rows(request, resource))


class RndResourceUnshareView(APIView):
    """DELETE → stop sharing a resource with one client."""

    permission_classes = [IsRnd]

    def delete(self, request, pk, relationship_id):
        share = get_object_or_404(
            ResourceShare, resource__pk=pk, resource__uploaded_by=request.user, relationship_id=relationship_id
        )
        share.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientResourceListView(generics.ListAPIView):
    """Active resources an RND has shared with this client, while that
    RND relationship is still active (confirmed). Uploading alone doesn't
    put anything here — the RND picks recipients via RndResourceShareView."""

    permission_classes = [IsClient]

    def get_serializer_class(self):
        from .serializers import ClientResourceSerializer

        return ClientResourceSerializer

    def get_queryset(self):
        from django.db.models import Prefetch

        mine = ResourceShare.objects.filter(
            relationship__client=self.request.user, relationship__status=RndClientRelationship.Status.ACTIVE,
        ).order_by("-shared_at")
        return (
            Resource.objects.filter(
                is_active=True,
                shares__relationship__client=self.request.user,
                shares__relationship__status=RndClientRelationship.Status.ACTIVE,
            )
            .select_related("uploaded_by")
            .prefetch_related(Prefetch("shares", queryset=mine, to_attr="_my_shares"))
            .distinct()
            .order_by("-created_at")
        )
