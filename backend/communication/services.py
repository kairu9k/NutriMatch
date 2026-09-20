import cloudinary
import cloudinary.uploader
from django.conf import settings

from .models import NotificationLog


class ResourceUploadError(Exception):
    pass


class CloudinaryResourceUploadService:
    """Uploads a Resource's file (PDF/video/etc.) to Cloudinary and returns
    the resulting secure URL as a plain string, to be stored in
    Resource.file_path (varchar per vault/database.txt) — this does not
    route through Django's FileField/DEFAULT_FILE_STORAGE machinery."""

    def __init__(self):
        cfg = settings.CLOUDINARY
        self.cloud_name = cfg["CLOUD_NAME"]
        self.api_key = cfg["API_KEY"]
        self.api_secret = cfg["API_SECRET"]

    def upload(self, file, *, folder="resources") -> str:
        if not (self.cloud_name and self.api_key and self.api_secret):
            raise ResourceUploadError(
                "Cloudinary is not configured — set CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in .env."
            )
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )
        try:
            # resource_type="auto" lets Cloudinary accept PDFs/videos, not
            # just images — it would otherwise reject non-image uploads.
            result = cloudinary.uploader.upload(file, folder=folder, resource_type="auto")
        except cloudinary.exceptions.Error as exc:
            raise ResourceUploadError(f"Cloudinary upload failed: {exc}") from exc
        return result["secure_url"]


def notify(recipient, notifiable_type, notifiable_id, subject, content):
    """Creates an in-app notification. IN_APP notifications are considered
    delivered immediately — there's no external delivery step to track."""
    return NotificationLog.objects.create(
        recipient=recipient,
        notifiable_type=notifiable_type,
        notifiable_id=notifiable_id,
        channel=NotificationLog.Channel.IN_APP,
        subject=subject,
        content=content,
        status=NotificationLog.Status.DELIVERED,
    )
