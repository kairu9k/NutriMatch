"""Private meal-log photos (2026-10-19, user's call — RA 10173: a meal photo
is health data).

Photos are stored as *authenticated* Cloudinary assets, so their normal
address doesn't work. Whoever may see a meal log (the client who logged it,
or that client's RND — the views already enforce that) gets a Cloudinary
download link that expires after PHOTO_LINK_MINUTES. Photos uploaded before
this change keep their public `photo_url` until
`manage.py make_meal_photos_private` moves them.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

FOLDER = "meal-logs-private"
PHOTO_LINK_MINUTES = 10
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_BYTES = 10 * 1024 * 1024


class MealPhotoError(Exception):
    pass


def _configure():
    import cloudinary

    cfg = settings.CLOUDINARY
    if not (cfg["CLOUD_NAME"] and cfg["API_KEY"] and cfg["API_SECRET"]):
        raise MealPhotoError("Photo storage isn't set up yet (Cloudinary keys missing in .env).")
    cloudinary.config(cloud_name=cfg["CLOUD_NAME"], api_key=cfg["API_KEY"], api_secret=cfg["API_SECRET"], secure=True)


def upload_meal_photo(file):
    """Store the photo privately. Returns (public_id, format)."""
    import cloudinary.exceptions
    import cloudinary.uploader

    content_type = getattr(file, "content_type", "") or ""
    if content_type and content_type not in ALLOWED_TYPES:
        raise MealPhotoError("Use a photo (JPG, PNG, WEBP or HEIC).")
    if getattr(file, "size", 0) > MAX_BYTES:
        raise MealPhotoError("The photo must be 10 MB or smaller.")
    _configure()
    try:
        result = cloudinary.uploader.upload(file, folder=FOLDER, resource_type="image", type="authenticated")
    except cloudinary.exceptions.Error as exc:
        raise MealPhotoError(f"Could not upload the photo: {exc}") from exc
    return result["public_id"], result.get("format") or "jpg"


PHOTO_SALT = "meal-photo"


def meal_photo_link(log):
    """A link to the log's photo that works for PHOTO_LINK_MINUTES, or None.
    Only call it for someone allowed to see the log.

    The link is the API's own (/api/meal-photos/<id>/?t=<signed token>): the
    token expires after PHOTO_LINK_MINUTES and the API fetches the photo from
    Cloudinary's CDN, which is fast (Cloudinary's own expiring download link
    took ~16 s per photo from here, 2026-10-24)."""
    if log.photo_public_id:
        from django.core import signing

        token = signing.dumps({"l": log.id}, salt=PHOTO_SALT)
        return f"{settings.API_PUBLIC_URL}/api/meal-photos/{log.id}/?t={token}"
    return log.photo_url or None  # older photo not moved yet


def read_photo_token(token, log_id):
    """True when `token` was issued for this log in the last PHOTO_LINK_MINUTES."""
    from django.core import signing

    try:
        data = signing.loads(token or "", salt=PHOTO_SALT, max_age=PHOTO_LINK_MINUTES * 60)
    except signing.BadSignature:
        return False
    return data.get("l") == log_id


def fetch_meal_photo(log):
    """The photo's bytes, or None."""
    from core.downloads import fetch_private_image

    try:
        _configure()
    except MealPhotoError:
        return None
    return fetch_private_image(log.photo_public_id, log.photo_format or "jpg",
                               int((timezone.now() + timedelta(minutes=1)).timestamp()))


def destroy_meal_photo(public_id, *, authenticated=True):
    """Best effort — a failed delete leaves an orphan asset, never an error."""
    if not public_id:
        return
    try:
        import cloudinary.uploader

        _configure()
        cloudinary.uploader.destroy(public_id, resource_type="image",
                                    type="authenticated" if authenticated else "upload", invalidate=True)
    except Exception:
        logger.exception("Could not delete meal photo %s", public_id)
