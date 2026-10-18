from django.conf import settings
from django.db import models

from scheduling.models import RndClientRelationship


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        FILE = "file", "File"
        IMAGE = "image", "Image"
        SYSTEM = "system", "System"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    attachment_url = models.CharField(max_length=1000, null=True, blank=True)
    attachment_type = models.CharField(max_length=50, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"

    def __str__(self):
        return f"Message from {self.sender.full_name} ({self.created_at:%Y-%m-%d %H:%M})"


class Resource(models.Model):
    class Type(models.TextChoices):
        ARTICLE = "article", "Article"
        PDF = "pdf", "PDF"
        VIDEO = "video", "Video"
        LINK = "link", "Link"

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_resources"
    )
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.ARTICLE)
    file_path = models.CharField(max_length=500, null=True, blank=True)
    url = models.CharField(max_length=1000, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resources"

    def __str__(self):
        return self.title


class ResourceShare(models.Model):
    """A resource the RND chose to send to one of their clients (2026-10-11).
    Uploading alone shares nothing — clients only see resources with a row
    here. It points at the relationship, not the client, so a resource can
    only go to the RND's own matched clients, and a client loses access once
    the relationship stops being active."""

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="shares")
    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="resource_shares"
    )
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resource_shares"
        constraints = [
            models.UniqueConstraint(fields=["resource", "relationship"], name="unique_resource_share"),
        ]

    def __str__(self):
        return f"{self.resource} → relationship {self.relationship_id}"


class Reminder(models.Model):
    """Scheduled reminders to a client (proposal: automated reminder module).

    Two kinds share this table:
    - automatic ones (appointment / payment / meal logging) written by
      communication/reminders.py when they're sent — `source_key` makes each
      one unique so it's never sent twice;
    - ones an RND sets for a client (`created_by`), e.g. medication cues or
      habit prompts, which can repeat; `send_at` is the next time it fires.
    """

    class Type(models.TextChoices):
        APPOINTMENT = "appointment", "Appointment"
        PAYMENT = "payment", "Payment"
        MEAL_LOG = "meal_log", "Meal Log"
        MEDICATION = "medication", "Medication"
        GENERAL = "general", "General"

    class Repeat(models.TextChoices):
        ONCE = "once", "Once"
        DAILY = "daily", "Every day"
        WEEKDAYS = "weekdays", "Weekdays"
        WEEKLY = "weekly", "Every week"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders"
    )
    title = models.CharField(max_length=255)
    message = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.GENERAL)
    send_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # RND-set reminders
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="reminders_created"
    )
    relationship = models.ForeignKey(
        "scheduling.RndClientRelationship", on_delete=models.CASCADE, null=True, blank=True, related_name="reminders"
    )
    repeat = models.CharField(max_length=10, choices=Repeat.choices, default=Repeat.ONCE)
    # The PH date the client last ticked this task off in "My tasks" (done for
    # that day; a repeating task starts unticked again the next day).
    done_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # the RND paused it
    is_muted = models.BooleanField(default=False)  # the client muted it
    last_sent_at = models.DateTimeField(null=True, blank=True)
    # automatic reminders: e.g. "appt:12:24h" — one row per reminder sent
    source_key = models.CharField(max_length=100, null=True, blank=True, unique=True)

    class Meta:
        db_table = "reminders"

    def __str__(self):
        return f"{self.title} — {self.send_at:%Y-%m-%d %H:%M}"


class ReminderPreference(models.Model):
    """A client's reminder settings (Profile Settings > Notifications &
    reminders). In-app notifications are always on; email is opt-in."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminder_preference")
    appointments = models.BooleanField(default=True)
    payments = models.BooleanField(default=True)
    meal_logging = models.BooleanField(default=True)
    rnd_reminders = models.BooleanField(default=True)
    email = models.BooleanField(default=False)
    # SMS to the client's mobile number (Semaphore) — opt-in like email; only
    # consultation, payment and RND-set reminders (not meal logging).
    sms = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reminder_preferences"

    @classmethod
    def for_user(cls, user):
        pref, _ = cls.objects.get_or_create(user=user)
        return pref


class NotificationLog(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"
        IN_APP = "in_app", "In App"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        BOUNCED = "bounced", "Bounced"

    notifiable_type = models.CharField(max_length=100, null=True, blank=True)
    notifiable_id = models.IntegerField(null=True, blank=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_logs"
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    subject = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_logs"

    def __str__(self):
        return f"{self.channel} to {self.recipient.full_name} ({self.status})"


class SupportTicket(models.Model):
    """A Help & Support request from a client or RND to the NutriMatch admins
    (message-and-reply, not live chat). Added after the proposal's schema."""

    class Category(models.TextChoices):
        PAYMENT = "payment", "Payment or refund"
        APPOINTMENT = "appointment", "Appointment"
        ACCOUNT = "account", "Account"
        REPORT = "report", "Report a user"
        TECHNICAL = "technical", "Technical problem"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"  # waiting for the admins
        ANSWERED = "answered", "Answered"  # an admin replied, waiting for the user
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")
    category = models.CharField(max_length=20, choices=Category.choices)
    subject = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    appointment = models.ForeignKey("scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    user_unread = models.BooleanField(default=False)  # an admin reply the user hasn't opened
    admin_unread = models.BooleanField(default=True)  # a user message no admin has opened
    last_activity_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_tickets"
        ordering = ["-last_activity_at"]

    def __str__(self):
        return f"Support #{self.id}: {self.subject}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    is_admin = models.BooleanField(default=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_messages"
        ordering = ["created_at"]
