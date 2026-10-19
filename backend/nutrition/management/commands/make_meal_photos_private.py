"""Move meal-log photos uploaded before 2026-10-19 (public Cloudinary
images) to private storage: re-upload each as an authenticated asset, then
delete the public copy so its old address stops working.

    python manage.py make_meal_photos_private [--dry-run]

Safe to run again — logs already moved are skipped."""

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from nutrition.models import MealLog
from nutrition.photos import FOLDER, MealPhotoError, _configure, destroy_meal_photo

# https://res.cloudinary.com/<cloud>/image/upload/[<transformations>/]v123/<public_id>.<ext>
_PUBLIC_ID = re.compile(r"/image/upload/(?:[^/]+/)*?v\d+/(.+)\.[A-Za-z0-9]+$")


def public_id_from_url(url):
    m = _PUBLIC_ID.search(url or "")
    return m.group(1) if m else None


class Command(BaseCommand):
    help = "Make meal-log photos private (authenticated Cloudinary assets)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list what would move.")

    def handle(self, *args, dry_run=False, **options):
        import cloudinary.exceptions
        import cloudinary.uploader

        logs = MealLog.objects.filter(photo_public_id__isnull=True).exclude(photo_url__isnull=True).exclude(photo_url="")
        total = logs.count()
        self.stdout.write(f"{total} meal photo(s) still public.")
        if dry_run or not total:
            return
        _configure()
        moved = failed = 0
        for log in logs:
            try:
                result = cloudinary.uploader.upload(log.photo_url, folder=FOLDER, resource_type="image", type="authenticated")
            except (cloudinary.exceptions.Error, MealPhotoError) as exc:
                failed += 1
                self.stderr.write(f"  meal log {log.id}: could not copy ({exc}) — left as it was")
                continue
            old_public = public_id_from_url(log.photo_url)
            with transaction.atomic():
                MealLog.objects.filter(pk=log.pk).update(
                    photo_public_id=result["public_id"], photo_format=result.get("format") or "jpg", photo_url=None,
                )
            if old_public:
                destroy_meal_photo(old_public, authenticated=False)
            moved += 1
            self.stdout.write(f"  meal log {log.id}: now private")
        self.stdout.write(self.style.SUCCESS(f"Done: {moved} moved, {failed} failed."))
