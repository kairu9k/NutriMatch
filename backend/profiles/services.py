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
