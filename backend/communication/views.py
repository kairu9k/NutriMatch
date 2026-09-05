from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from scheduling.models import RndClientRelationship

from .models import Message
from .serializers import MessageSerializer


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
