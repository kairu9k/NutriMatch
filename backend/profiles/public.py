"""What clients see about an RND (Find an RND + the RND profile page).

Only public profile information — no email, phone or internal account
fields (RA 10173 data minimization). The PRC license number stays: it's
public in the PRC registry and lets a client double-check the RND."""

from datetime import datetime, time, timedelta

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import serializers

from scheduling.models import Appointment, Review, RndClientRelationship

from .models import LANGUAGES, RND_SPECIALIZATIONS, RndProfile

# Same session length and slot step as the booking pop-up (RndProfileView.vue).
SESSION_MINUTES = 60
SLOT_STEP_MINUTES = 15
SLOT_LOOKAHEAD_DAYS = 28


def _ph():
    from scheduling.serializers import PH_TZ

    return PH_TZ


def next_open_slots(rnd_id, count=3, now=None):
    """The next `count` bookable 60-minute starts (15-minute steps, at least
    MIN_BOOKING_LEAD_MINUTES away; ISO, aware) inside the
    RND's weekly hours that don't overlap their pending/confirmed bookings."""
    from scheduling.serializers import MIN_BOOKING_LEAD_MINUTES

    from .models import RndAvailabilitySchedule

    ph = _ph()
    now = now or timezone.now()
    blocks = list(RndAvailabilitySchedule.objects.filter(rnd_id=rnd_id, is_available=True))
    if not blocks:
        return []
    horizon = now + timedelta(days=SLOT_LOOKAHEAD_DAYS)
    booked = [
        (a.scheduled_at, a.scheduled_at + timedelta(minutes=a.duration_minutes or SESSION_MINUTES))
        for a in Appointment.objects.filter(
            relationship__rnd_id=rnd_id, status__in=["pending", "confirmed"],
            scheduled_at__gte=now - timedelta(hours=3), scheduled_at__lt=horizon,
        )
    ]
    slots = []
    today = now.astimezone(ph).date()
    for offset in range(SLOT_LOOKAHEAD_DAYS):
        day = today + timedelta(days=offset)
        dow = (day.weekday() + 1) % 7  # Sunday=0, like the app
        starts = set()
        for b in blocks:
            if b.day_of_week != dow or b.effective_from > day or (b.effective_to and b.effective_to < day):
                continue
            start = datetime.combine(day, b.start_time, tzinfo=ph)
            block_end = datetime.combine(day, b.end_time, tzinfo=ph)
            while start + timedelta(minutes=SESSION_MINUTES) <= block_end:
                starts.add(start)
                start += timedelta(minutes=SLOT_STEP_MINUTES)
        for start in sorted(starts):
            end = start + timedelta(minutes=SESSION_MINUTES)
            if start < now + timedelta(minutes=MIN_BOOKING_LEAD_MINUTES) or any(s < end and e > start for s, e in booked):
                continue
            slots.append(start.isoformat())
            if len(slots) >= count:
                return slots
    return slots


class PublicRndProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    consultations_completed = serializers.SerializerMethodField()
    active_patients = serializers.SerializerMethodField()
    member_since = serializers.DateTimeField(source="user.created_at", read_only=True)
    next_open_slots = serializers.SerializerMethodField()
    clinic_address = serializers.SerializerMethodField()
    is_my_rnd = serializers.SerializerMethodField()
    booking_blocked_by = serializers.SerializerMethodField()

    class Meta:
        model = RndProfile
        fields = [
            "id", "user", "prc_license_number", "specialization", "bio", "consultation_fee", "consultation_modes",
            "available_for_new_clients", "verified_at", "languages", "average_rating", "review_count",
            "consultations_completed", "active_patients", "member_since", "next_open_slots", "clinic_address", "is_my_rnd", "booking_blocked_by",
        ]

    def get_user(self, obj):
        u = obj.user
        return {"id": u.id, "first_name": u.first_name, "last_name": u.last_name, "profile_photo": u.profile_photo}

    def get_languages(self, obj):
        return [{"code": lang.language_code, "language_name": lang.language_name} for lang in obj.user.languages.all()]

    def _reviews(self, obj):
        if not hasattr(obj, "_public_review_stats"):
            obj._public_review_stats = Review.objects.filter(rnd_id=obj.user_id, is_public=True).aggregate(
                avg=Avg("rating"), count=Count("id"))
        return obj._public_review_stats

    def get_average_rating(self, obj):
        avg = self._reviews(obj)["avg"]
        return round(float(avg), 1) if avg is not None else None

    def get_review_count(self, obj):
        return self._reviews(obj)["count"]

    def get_consultations_completed(self, obj):
        return Appointment.objects.filter(relationship__rnd_id=obj.user_id, status="completed").count()

    def get_active_patients(self, obj):
        return RndClientRelationship.objects.filter(rnd_id=obj.user_id, status="active").count()

    def get_next_open_slots(self, obj):
        return next_open_slots(obj.user_id, count=self.context.get("slot_count", 3))

    def get_clinic_address(self, obj):
        # Only meaningful (and only shown) when they consult in person.
        return obj.clinic_address if "in_person" in (obj.consultation_modes or []) else None

    def get_booking_blocked_by(self, obj):
        """One RND at a time: {name, status} of the client's current RND when
        it's someone else (they can't book this RND yet), else None."""
        request = self.context.get("request")
        if not request or request.user.role != "client":
            return None
        cache = self.context.setdefault("_current_rnd", {})
        if "rel" not in cache:
            from scheduling.services import current_rnd_relationship

            cache["rel"] = current_rnd_relationship(request.user)
        rel = cache["rel"]
        if rel is None or rel.rnd_id == obj.user_id:
            return None
        return {"name": rel.rnd.full_name, "rnd_id": rel.rnd_id, "status": rel.status}

    def get_is_my_rnd(self, obj):
        request = self.context.get("request")
        if not request or request.user.role != "client":
            return False
        return RndClientRelationship.objects.filter(
            rnd_id=obj.user_id, client=request.user, status__in=["active", "pending"]).exists()


class PublicRndDetailSerializer(PublicRndProfileSerializer):
    """The profile page also gets the star breakdown."""

    rating_breakdown = serializers.SerializerMethodField()

    class Meta(PublicRndProfileSerializer.Meta):
        fields = PublicRndProfileSerializer.Meta.fields + ["rating_breakdown"]

    def get_rating_breakdown(self, obj):
        counts = dict(Review.objects.filter(rnd_id=obj.user_id, is_public=True)
                      .values_list("rating").annotate(n=Count("id")))
        return {str(star): counts.get(star, 0) for star in (5, 4, 3, 2, 1)}


MODE_LABELS = [("video", "Video call"), ("chat", "Chat"), ("in_person", "In-person")]


def search_options():
    """Filter choices for Find an RND — only values some RND a client can
    find actually has (user's rule, 2026-10-13), in the registration lists'
    order. RND registration/Profile Settings keep the full lists."""
    from .models import RndLanguage
    from .services import bookable_rnd_profiles

    profiles = list(bookable_rnd_profiles().filter(available_for_new_clients=True))
    specs = {p.specialization for p in profiles if p.specialization}
    codes = set(RndLanguage.objects.filter(rnd_id__in=[p.user_id for p in profiles]).values_list("language_code", flat=True))
    modes = {m for p in profiles for m in (p.consultation_modes or [])}
    return {
        "specializations": [s for s in RND_SPECIALIZATIONS if s in specs] + sorted(specs - set(RND_SPECIALIZATIONS)),
        "languages": [{"code": code, "label": label} for code, label in LANGUAGES if code in codes],
        "modes": [{"value": v, "label": label} for v, label in MODE_LABELS if v in modes],
    }
