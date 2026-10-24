from django.db.models import Count, OuterRef, Prefetch, Q, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from scheduling.models import RndClientRelationship

from .models import Message, NotificationLog, Resource, ResourceShare
from .serializers import MessageSerializer, NotificationDetailSerializer, NotificationLogSerializer, ResourceSerializer
from .live import group_send, push_new_message
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
        qs = Message.objects.filter(
            relationship=relationship, deleted_at__isnull=True
        ).select_related("sender").order_by("created_at")
        # ?after=<id>: only newer messages (the chat polls with this when the
        # live connection isn't available, e.g. no Redis).
        after = self.request.query_params.get("after")
        if after and after.isdigit():
            qs = qs.filter(id__gt=int(after))
        return qs

    def create(self, request, *args, **kwargs):
        relationship = self.get_relationship()
        # Chat is open only while care is active — i.e. after the RND
        # confirmed a booking (user's rule, 2026-10-15).
        if relationship.status == RndClientRelationship.Status.DISCHARGED:
            raise PermissionDenied("This care plan has ended, so new messages can't be sent. Book a consultation to start again.")
        if relationship.status != RndClientRelationship.Status.ACTIVE:
            raise PermissionDenied("You can message once the RND confirms the booking.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(relationship=relationship, sender=request.user)
        # No bell notification: unread chat shows on the Messages icon instead
        # (MessageUnreadView), so the bell keeps bookings, payments, plans…

        data = MessageSerializer(message).data
        _broadcast_later(relationship.id, data)
        recipient_id = relationship.client_id if request.user.id == relationship.rnd_id else relationship.rnd_id
        push_new_message(recipient_id, data)
        return Response(data, status=status.HTTP_201_CREATED)


def _broadcast_later(relationship_id, message_data):
    """Also push a message sent over the API to anyone connected live to that
    chat (MessageConsumer); without a connection the page polls instead."""
    group_send(f"relationship_{relationship_id}", {"type": "chat.message", "message": message_data})


def _my_relationships(user):
    return RndClientRelationship.objects.filter(Q(rnd=user) | Q(client=user))


def _unread_from_others(user):
    return Message.objects.filter(
        relationship__in=_my_relationships(user), is_read=False, deleted_at__isnull=True,
    ).exclude(sender=user)


class MessageUnreadView(APIView):
    """GET → {total, by_relationship: {<id>: n}, latest: {<id>: {message,
    created_at, sender_id}}} — chat messages from the other person not read
    yet (the dot on the top-bar Messages icon and on each conversation), plus
    every chat's latest message for the Messages page's list previews."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rows = _unread_from_others(request.user).values("relationship_id").annotate(n=Count("id"))
        by_rel = {str(r["relationship_id"]): r["n"] for r in rows}
        last_id = (Message.objects.filter(relationship=OuterRef("pk"), deleted_at__isnull=True)
                   .order_by("-created_at", "-id").values("id")[:1])
        ids = (_my_relationships(request.user).annotate(last_id=Subquery(last_id))
               .exclude(last_id=None).values_list("last_id", flat=True))
        latest = {
            str(m.relationship_id): {"message": m.message[:200], "created_at": m.created_at, "sender_id": m.sender_id}
            for m in Message.objects.filter(id__in=list(ids))
        }
        return Response({"total": sum(by_rel.values()), "by_relationship": by_rel, "latest": latest})


class MessageMarkReadView(APIView):
    """POST → marks the other person's messages in this chat as read (the
    Messages page calls it when a conversation is open)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, relationship_id):
        relationship = get_object_or_404(_my_relationships(request.user), id=relationship_id)
        marked = _unread_from_others(request.user).filter(relationship=relationship).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({"marked": marked})


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
        # Chat isn't in the bell (it's on the Messages icon) — this also hides
        # "New message" notifications stored before that change.
        return NotificationLog.objects.filter(
            recipient=self.request.user, channel=NotificationLog.Channel.IN_APP
        ).exclude(notifiable_type="message").order_by("-created_at")

    # ?page=N (the Notifications page): {count, unread, page, page_size, results}
    # PAGE_SIZE at a time. Without ?page (bell, dashboard) the plain list as before.
    PAGE_SIZE = 20

    def list(self, request, *args, **kwargs):
        if "page" not in request.query_params:
            return super().list(request, *args, **kwargs)
        qs = self.get_queryset()
        try:
            page = max(1, int(request.query_params.get("page") or 1))
        except ValueError:
            page = 1
        count = qs.count()
        last = max(1, -(-count // self.PAGE_SIZE))
        page = min(page, last)
        rows = qs[(page - 1) * self.PAGE_SIZE: page * self.PAGE_SIZE]
        return Response({
            "count": count,
            "unread": qs.filter(is_read=False).count(),
            "page": page,
            "page_size": self.PAGE_SIZE,
            "results": self.get_serializer(rows, many=True).data,
        })


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
    it's currently shared with, and those clients (`_active_shares`, for the
    faces on each row of the Resources list)."""
    active = RndClientRelationship.Status.ACTIVE
    return Resource.objects.filter(uploaded_by=user).annotate(
        _shared_count=Count("shares", filter=Q(shares__relationship__status=active))
    ).prefetch_related(Prefetch(
        "shares",
        queryset=ResourceShare.objects.filter(relationship__status=active)
        .select_related("relationship__client").order_by("-shared_at"),
        to_attr="_active_shares",
    ))


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
