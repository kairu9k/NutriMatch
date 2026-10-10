"""Onboarding status per role (client: strict 4-step onboarding; RND: the
application is reviewed before they can sign in, so an approved RND is
onboarded — only setup gaps on older accounts are reported)."""

from .models import User


def _client_steps(user):
    from clinical.models import PreConsultationScreening
    from profiles.models import ClientHealthProfile, ClientProfile

    profile = ClientProfile.objects.filter(user=user).first()
    health = ClientHealthProfile.objects.filter(user=user).first()
    return [
        {"key": "welcome", "label": "Welcome", "required": False, "done": True},
        {"key": "about", "label": "Your date of birth and sex", "required": True,
         "done": bool(profile and profile.date_of_birth and profile.sex)},
        {"key": "health", "label": "Your food allergies (or \"none\")", "required": True,
         "done": bool(health and health.allergies is not None)},
        {"key": "screening", "label": "Your health screening", "required": True,
         "done": PreConsultationScreening.objects.filter(client=user).exists()},
    ]


def onboarding_status(user):
    data = {
        "role": user.role,
        "completed_at": user.onboarding_completed_at,
        "complete": user.onboarding_completed_at is not None,
        "steps": [],
        "missing": [],
    }
    if user.role == User.Role.CLIENT:
        data["steps"] = _client_steps(user)
    elif user.role == User.Role.RND:
        from profiles.services import rnd_missing_setup

        profile = getattr(user, "rnd_profile", None)
        data["missing"] = rnd_missing_setup(profile) if profile else []
    else:
        data["complete"] = True
    return data
