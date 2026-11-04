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
    # why the RND ended care (shown to the client); cleared if they're rebooked
    discharge_reason = models.TextField(null=True, blank=True)

    class EndedBy(models.TextChoices):
        RND = "rnd", "Discharged by the RND"
        AUTO = "auto", "Ended automatically (client's request)"
        ADMIN = "admin", "Ended by NutriMatch"

    ended_by = models.CharField(max_length=10, choices=EndedBy.choices, null=True, blank=True)

    # The client asked to end care (Profile Settings -> Care Team, 2026-10-19):
    # the RND has DISCHARGE_REQUEST_DAYS to discharge them, then it ends on its
    # own (scheduling/discharge_requests.py). Added after the proposal.
    class RequestReason(models.TextChoices):
        DIFFERENT_RND = "different_rnd", "I want a different RND"
        GOAL_REACHED = "goal_reached", "I reached my goal"
        MOVED = "moved", "I'm moving or no longer available"
        SCHEDULE = "schedule", "The schedule doesn't work for me"
        COST = "cost", "Cost"
        OTHER = "other", "Other"

    discharge_requested_at = models.DateTimeField(null=True, blank=True)
    discharge_request_reason = models.CharField(max_length=20, choices=RequestReason.choices, null=True, blank=True)
    discharge_request_note = models.TextField(null=True, blank=True)
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
        # The paid client didn't come (2026-11-02, user's rule): no refund
        # unless they win a dispute; the RND is paid like a completed one.
        NO_SHOW = "no_show", "No-show"

    class CancelledBy(models.TextChoices):
        CLIENT = "client", "The client"
        RND = "rnd", "The RND"
        ADMIN = "admin", "NutriMatch"
        SYSTEM = "system", "Automatically"
        RND_ABSENT = "rnd_absent", "The RND didn't attend"
        CALL_FAILED = "call_failed", "The video call didn't work"

    class CancelCategory(models.TextChoices):
        EMERGENCY = "emergency", "Emergency (family or health)"
        TECHNICAL = "technical", "Technical problem"
        OTHER = "other", "Other"

    class DisputeOutcome(models.TextChoices):
        REFUNDED = "refunded", "Refunded"
        REJECTED = "rejected", "Rejected"

    class Service(models.TextChoices):
        # What the client paid for (2026-11-04, user's call). Bookings made
        # before this existed count as consultation + meal plan.
        CONSULTATION = "consultation", "Consultation only"
        CONSULTATION_MEAL_PLAN = "consultation_meal_plan", "Consultation + meal plan"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="appointments"
    )
    service = models.CharField(max_length=30, choices=Service.choices, default=Service.CONSULTATION)
    scheduled_at = models.DateTimeField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.VIDEO)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    duration_minutes = models.SmallIntegerField(null=True, blank=True)
    video_session_url = models.CharField(max_length=1000, null=True, blank=True)
    meeting_id = models.CharField(max_length=255, null=True, blank=True)
    cancellation_reason = models.CharField(max_length=500, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    # When the RND marked it completed (or a no-show) — starts the 3-day payout hold.
    completed_at = models.DateTimeField(null=True, blank=True)

    # How it was cancelled (2026-11-02; older rows are empty). A late cancel
    # is an RND cancelling a confirmed consultation in its last 30 minutes.
    cancelled_by = models.CharField(max_length=20, choices=CancelledBy.choices, null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_category = models.CharField(max_length=20, choices=CancelCategory.choices, null=True, blank=True)
    cancelled_late = models.BooleanField(default=False)

    # Attendance in the video call, recorded by the server from the call's
    # signaling socket (scheduling/attendance.py). Join/leave times only:
    # nothing from the call itself is kept (RA 10173).
    rnd_joined_at = models.DateTimeField(null=True, blank=True)
    client_joined_at = models.DateTimeField(null=True, blank=True)
    rnd_left_at = models.DateTimeField(null=True, blank=True)
    client_left_at = models.DateTimeField(null=True, blank=True)
    together_seconds = models.PositiveIntegerField(default=0)
    together_since = models.DateTimeField(null=True, blank=True)  # both are in the call right now
    # each person's total time in the call (they can leave and come back)
    rnd_seconds = models.PositiveIntegerField(default=0)
    client_seconds = models.PositiveIntegerField(default=0)
    rnd_in_since = models.DateTimeField(null=True, blank=True)  # in the call right now
    client_in_since = models.DateTimeField(null=True, blank=True)

    # The client disputes a no-show (3 days); the payout waits until an admin decides.
    dispute_opened_at = models.DateTimeField(null=True, blank=True)
    dispute_reason = models.TextField(null=True, blank=True)
    dispute_resolved_at = models.DateTimeField(null=True, blank=True)
    dispute_outcome = models.CharField(max_length=10, choices=DisputeOutcome.choices, null=True, blank=True)
    dispute_note = models.TextField(null=True, blank=True)
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
        WEBRTC = "webrtc", "NutriMatch video (WebRTC)"
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
        max_length=20, choices=VideoProvider.choices, default=VideoProvider.JITSI
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
