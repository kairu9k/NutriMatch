from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from scheduling.models import RndClientRelationship

from .models import Message, NotificationLog
from .serializers import MessageSerializer, NotificationLogSerializer
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
