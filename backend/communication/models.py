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


class Reminder(models.Model):
    class Type(models.TextChoices):
        APPOINTMENT = "appointment", "Appointment"
        MEAL_LOG = "meal_log", "Meal Log"
        MEDICATION = "medication", "Medication"
        GENERAL = "general", "General"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders"
    )
    title = models.CharField(max_length=255)
    message = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.GENERAL)
    send_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reminders"

    def __str__(self):
        return f"{self.title} — {self.send_at:%Y-%m-%d %H:%M}"


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
