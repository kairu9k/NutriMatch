"""What an admin sees on a user's detail page (AdminUserOverviewView)."""

from collections import Counter

from .models import User


def _counts(qs, field="status"):
    return dict(Counter(qs.values_list(field, flat=True)))


def user_overview(user, *, viewer, request=None):
    from core.models import AuditLog
    from scheduling.models import Appointment, Review

    from .serializers import UserSerializer

    data = {
        "user": UserSerializer(user).data,
        "account": {
            "is_active": user.is_active,
            "last_login": user.last_login,
            "email_verified_at": user.email_verified_at,
            "terms_accepted_at": getattr(user, "terms_accepted_at", None),
            "data_consent_at": getattr(user, "data_consent_at", None),
            "onboarding_completed_at": user.onboarding_completed_at,
            "deleted_at": getattr(user, "deleted_at", None),
        },
        "client": None,
        "rnd": None,
        "recent_activity": [
            {"action": a.action, "created_at": a.created_at, "by": a.user.full_name if a.user else None}
            for a in AuditLog.objects.filter(record_id=user.pk, table_name="users").select_related("user").order_by("-created_at")[:10]
        ],
    }

    if user.role == User.Role.CLIENT:
        from billing.models import Invoice
        from clinical.models import PreConsultationScreening
        from profiles.models import ClientHealthProfile, ClientProfile
        from scheduling.models import RndClientRelationship

        profile = ClientProfile.objects.filter(user=user).first()
        health = ClientHealthProfile.objects.filter(user=user).first()
        latest = PreConsultationScreening.objects.filter(client=user).order_by("-created_at").first()
        appts = Appointment.objects.filter(relationship__client=user)
        invoices = Invoice.objects.filter(relationship__client=user)
        rels = RndClientRelationship.objects.filter(client=user).select_related("rnd")
        data["client"] = {
            "profile": {
                "date_of_birth": profile.date_of_birth if profile else None,
                "sex": profile.sex if profile else None,
                "language_code": profile.language_code if profile else None,
                "address": profile.address if profile else None,
                "emergency_contact": profile.emergency_contact if profile else None,
                "emergency_phone": profile.emergency_phone if profile else None,
            },
            "health": {
                "medical_conditions": health.medical_conditions if health else None,
                "allergies": health.allergies if health else None,
                "dietary_restrictions": health.dietary_restrictions if health else None,
                "health_goals": health.health_goals if health else None,
                "religion": health.religion if health else None,
            },
            "latest_screening": {
                "created_at": latest.created_at, "height_cm": latest.height_cm, "weight_kg": latest.weight_kg,
                "bmi": latest.bmi, "bmi_category": latest.bmi_category, "tdee_kcal": latest.tdee_kcal,
                "nrs_score": latest.nrs_score, "nrs_risk": latest.nrs_risk,
            } if latest else None,
            "screening_count": PreConsultationScreening.objects.filter(client=user).count(),
            "appointments": _counts(appts),
            "invoices": {
                "paid_total": sum(i.amount for i in invoices.filter(status="paid")),
                **_counts(invoices),
            },
            "rnds": [
                {"rnd_id": r.rnd_id, "name": r.rnd.full_name, "status": r.status} for r in rels
            ],
        }
        # Health information was shown — record who looked (RA 10173).
        AuditLog.objects.create(
            user=viewer, action="client.record_viewed", table_name="users", record_id=user.pk,
            ip_address=(request.META.get("REMOTE_ADDR") if request else None),
        )

    elif user.role == User.Role.RND:
        from billing.models import Payout
        from billing.payouts import rnd_earnings
        from profiles.services import prc_license_image_url, rnd_missing_setup
        from scheduling.models import RndClientRelationship

        profile = getattr(user, "rnd_profile", None)
        account = getattr(user, "payout_account", None)
        earnings = rnd_earnings(user)
        reviews = Review.objects.filter(rnd=user)
        data["rnd"] = {
            "profile": {
                "prc_license_number": profile.prc_license_number if profile else None,
                "prc_license_image_url": prc_license_image_url(profile.prc_license_image) if profile else None,
                "specialization": profile.specialization if profile else None,
                "bio": profile.bio if profile else None,
                "consultation_fee": profile.consultation_fee if profile else None,
                "consultation_modes": profile.consultation_modes if profile else [],
                "available_for_new_clients": profile.available_for_new_clients if profile else None,
                "review_status": profile.review_status if profile else None,
                "rejection_reason": profile.rejection_reason if profile else None,
                "verified_at": profile.verified_at if profile else None,
                "date_of_birth": profile.date_of_birth if profile else None,
                "clinic_address": profile.clinic_address if profile else None,
            },
            "languages": [lang.language_name for lang in user.languages.all()],
            "availability": [
                {"day_of_week": b.day_of_week, "start_time": b.start_time.strftime("%H:%M"), "end_time": b.end_time.strftime("%H:%M")}
                for b in user.availability_schedules.filter(is_available=True).order_by("day_of_week", "start_time")
            ],
            "missing_setup": rnd_missing_setup(profile) if profile else [],
            "payout_account": {
                "method": account.method, "method_label": account.get_method_display(), "account_name": account.account_name,
                "account_number": account.account_number, "bank_name": account.bank_name, "updated_at": account.updated_at,
            } if account else None,
            "earnings": {k: earnings[k] for k in ("pending", "posted", "paid_out", "next_payout_date", "eligible")},
            "payouts": Payout.objects.filter(rnd=user).count(),
            "patients": RndClientRelationship.objects.filter(rnd=user, status="active").count(),
            "appointments": _counts(Appointment.objects.filter(relationship__rnd=user)),
            "rating": {
                "average": round(sum(r.rating for r in reviews) / reviews.count(), 1) if reviews.exists() else None,
                "count": reviews.count(),
            },
        }
    return data
