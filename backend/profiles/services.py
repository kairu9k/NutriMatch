import re

import cloudinary
import cloudinary.exceptions
import cloudinary.uploader
import cloudinary.utils
from django.conf import settings

ALLOWED_LICENSE_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_LICENSE_IMAGE_BYTES = 5 * 1024 * 1024


class LicenseImageUploadError(Exception):
    pass


def _configure():
    cfg = settings.CLOUDINARY
    if not (cfg["CLOUD_NAME"] and cfg["API_KEY"] and cfg["API_SECRET"]):
        raise LicenseImageUploadError(
            "Cloudinary is not configured — set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in .env."
        )
    cloudinary.config(
        cloud_name=cfg["CLOUD_NAME"], api_key=cfg["API_KEY"], api_secret=cfg["API_SECRET"], secure=True,
    )


def upload_prc_license_image(file) -> str:
    """Uploads an RND's PRC license photo as an *authenticated* Cloudinary
    asset — it shows the RND's face and ID, so it must not sit at a public
    URL (RA 10173). Returns the public_id; admins view it via
    prc_license_image_url()."""
    _configure()
    try:
        result = cloudinary.uploader.upload(
            file, folder="prc-licenses", resource_type="image", type="authenticated",
        )
    except cloudinary.exceptions.Error as exc:
        raise LicenseImageUploadError(f"Could not upload the license photo: {exc}") from exc
    return result["public_id"]


def prc_license_image_url(public_id: str | None) -> str | None:
    if not public_id:
        return None
    _configure()
    url, _ = cloudinary.utils.cloudinary_url(
        public_id, resource_type="image", type="authenticated", sign_url=True, secure=True,
    )
    return url


ALLOWED_PROFILE_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PROFILE_PHOTO_BYTES = 2 * 1024 * 1024
PROFILE_PHOTO_FOLDER = "profile-photos"
_PROFILE_PHOTO_ID = re.compile(r"/upload/(?:[^/]+/)*?(?:v\d+/)?(" + PROFILE_PHOTO_FOLDER + r"/[^/.]+)\.\w+$")


class ProfilePhotoUploadError(Exception):
    pass


def upload_profile_photo(file) -> str:
    """Uploads a user's profile photo and returns its URL (stored in
    User.profile_photo, per vault/database.txt). It's an avatar shown in the
    app, so it's a normal (public, unguessable) delivery URL — unlike the PRC
    license photo. Cropped to a 400x400 square on upload, so only a small
    avatar is kept rather than the original full-size picture."""
    try:
        _configure()
    except LicenseImageUploadError as exc:
        raise ProfilePhotoUploadError(str(exc)) from exc
    try:
        result = cloudinary.uploader.upload(
            file, folder=PROFILE_PHOTO_FOLDER, resource_type="image",
            transformation=[{"width": 400, "height": 400, "crop": "fill", "gravity": "face"}],
        )
    except cloudinary.exceptions.Error as exc:
        raise ProfilePhotoUploadError(f"Could not upload the photo: {exc}") from exc
    return result["secure_url"]


def destroy_profile_photo(url: str | None) -> None:
    """Best-effort delete of a replaced/removed profile photo. Only touches
    assets in our own profile-photos folder."""
    match = _PROFILE_PHOTO_ID.search(url or "")
    if not match:
        return
    try:
        _configure()
        cloudinary.uploader.destroy(match.group(1), resource_type="image", invalidate=True)
    except Exception:
        pass



# ---------------------------------------------------------------------------
# RND setup / listing rules (onboarding, 2026-10-10)
# ---------------------------------------------------------------------------

def bookable_rnd_profiles():
    """RNDs clients can find and book: approved, fee >= MIN_CONSULTATION_FEE,
    a bio, and at least one weekly availability block."""
    from .models import MIN_CONSULTATION_FEE, RndProfile

    return (
        RndProfile.objects.filter(
            is_verified=True,
            consultation_fee__gte=MIN_CONSULTATION_FEE,
            user__availability_schedules__is_available=True,
        )
        .exclude(bio__isnull=True)
        .exclude(bio="")
        .distinct()
    )


def rnd_missing_setup(profile):
    """What an RND still needs before clients can find/book them."""
    from .models import MIN_CONSULTATION_FEE

    missing = []
    if (profile.consultation_fee or 0) < MIN_CONSULTATION_FEE:
        missing.append({"key": "fee", "label": f"Set a consultation fee of at least \u20b1{MIN_CONSULTATION_FEE}"})
    if not (profile.bio or "").strip():
        missing.append({"key": "bio", "label": "Write your professional bio"})
    if not profile.user.availability_schedules.filter(is_available=True).exists():
        missing.append({"key": "availability", "label": "Add your weekly availability"})
    if not profile.user.languages.exists():
        missing.append({"key": "languages", "label": "Add the languages you consult in", "optional": True})
    return missing


def set_rnd_languages(user, codes):
    """Replace an RND's languages with `codes` (validated LANGUAGES codes)."""
    from .models import LANGUAGE_NAMES, RndLanguage

    RndLanguage.objects.filter(rnd=user).delete()
    RndLanguage.objects.bulk_create([
        RndLanguage(rnd=user, language_code=code, language_name=LANGUAGE_NAMES[code]) for code in codes
    ])
