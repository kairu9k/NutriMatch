from django.conf import settings
from django.db import models


class RndClientRelationship(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        DISCHARGED = "discharged", "Discharged"

    rnd = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_relationships"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rnd_relationships"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rnd_client_relationships"
        constraints = [
            models.UniqueConstraint(
                fields=["rnd", "client"], name="unique_rnd_client_pair"
            )
        ]

    def __str__(self):
        return f"{self.client.full_name} <-> {self.rnd.full_name} ({self.status})"


class Appointment(models.Model):
    class Type(models.TextChoices):
        IN_PERSON = "in_person", "In Person"
        VIDEO = "video", "Video"
        CHAT = "chat", "Chat"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="appointments"
    )
    scheduled_at = models.DateTimeField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.VIDEO)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    duration_minutes = models.SmallIntegerField(null=True, blank=True)
    video_session_url = models.CharField(max_length=1000, null=True, blank=True)
    meeting_id = models.CharField(max_length=255, null=True, blank=True)
    cancellation_reason = models.CharField(max_length=500, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"

    def __str__(self):
        return f"Appointment #{self.id} — {self.scheduled_at}"


class ConsultationSession(models.Model):
    class VideoProvider(models.TextChoices):
        ZOOM = "zoom", "Zoom"
        DAILY_CO = "daily_co", "Daily.co"
        JITSI = "jitsi", "Jitsi"
        TWILIO_VIDEO = "twilio_video", "Twilio Video"
        GOOGLE_MEET = "google_meet", "Google Meet"
        OTHER = "other", "Other"

    class SessionStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="consultation_sessions"
    )
    video_provider = models.CharField(
        max_length=20, choices=VideoProvider.choices, default=VideoProvider.DAILY_CO
    )
    external_session_id = models.CharField(max_length=255, null=True, blank=True)
    host_url = models.CharField(max_length=1000, null=True, blank=True)
    participant_url = models.CharField(max_length=1000, null=True, blank=True)
    recording_url = models.CharField(max_length=1000, null=True, blank=True)
    session_status = models.CharField(
        max_length=20, choices=SessionStatus.choices, default=SessionStatus.SCHEDULED
    )
    session_started_at = models.DateTimeField(null=True, blank=True)
    session_ended_at = models.DateTimeField(null=True, blank=True)
    actual_duration_min = models.SmallIntegerField(null=True, blank=True)
    provider_metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consultation_sessions"

    def __str__(self):
        return f"Session for Appointment #{self.appointment_id}"


class Review(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="review"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_given"
    )
    rnd = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received"
    )
    rating = models.SmallIntegerField(help_text="Scale 1-5")
    comment = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_range",
            )
        ]

    def __str__(self):
        return f"Review by {self.client.full_name} for {self.rnd.full_name} ({self.rating}★)"
