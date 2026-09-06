from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import RndClientRelationship

from .models import Message, NotificationLog, Resource
from .serializers import MessageSerializer, NotificationLogSerializer, ResourceSerializer
from .services import notify


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
        return NotificationLog.objects.filter(
            recipient=self.request.user, channel=NotificationLog.Channel.IN_APP
        ).order_by("-created_at")


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


class RndResourceListCreateView(generics.ListCreateAPIView):
    """RND's own uploaded resources. Create is currently restricted to
    'link' type — see ResourceSerializer.validate — since no file storage
    (MEDIA_ROOT/FileField) is configured anywhere in this project yet."""

    serializer_class = ResourceSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return Resource.objects.filter(uploaded_by=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class RndResourceUpdateView(generics.UpdateAPIView):
    """RND toggling their own resource active/inactive, or editing it."""

    serializer_class = ResourceSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return Resource.objects.filter(uploaded_by=self.request.user)


class ClientResourceListView(generics.ListAPIView):
    """Active resources shared by any RND the client has an active
    relationship with. Resource has no per-relationship scoping — it's a
    general library the RND shares with all their patients."""

    serializer_class = ResourceSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        rnd_ids = RndClientRelationship.objects.filter(
            client=self.request.user, status=RndClientRelationship.Status.ACTIVE
        ).values_list("rnd_id", flat=True)
        return Resource.objects.filter(
            uploaded_by_id__in=rnd_ids, is_active=True
        ).order_by("-created_at")
