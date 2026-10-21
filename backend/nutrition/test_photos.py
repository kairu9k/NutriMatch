"""Private meal-log photos (2026-10-19). Cloudinary is mocked — nothing is
uploaded. A photo is stored as an authenticated asset and only the client
and their RND get a link, which expires."""

from decimal import Decimal
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd
from scheduling.models import RndClientRelationship

from .management.commands.make_meal_photos_private import public_id_from_url
from .models import MealLog, MealPlan, MealPlanFoodItem, MealPlanMeal
from .photos import PHOTO_LINK_MINUTES

CLOUDINARY = {"CLOUD_NAME": "demo", "API_KEY": "123", "API_SECRET": "abc"}


def _jpeg(name="meal.jpg"):
    return SimpleUploadedFile(name, b"\xff\xd8\xff fake jpeg", content_type="image/jpeg")


@override_settings(CLOUDINARY=CLOUDINARY)
class PrivateMealPhotoTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.rnd = approve_rnd(User.objects.create_user(email="rp@nt.ph", password="x", role="rnd", first_name="M", last_name="S"))
        self.client_user = User.objects.create_user(email="cp@nt.ph", password="x", role="client", first_name="A", last_name="C")
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        plan = MealPlan.objects.create(relationship=rel, name="Plan", status="active")
        self.meal = MealPlanMeal.objects.create(meal_plan=plan, day_of_week=None, meal_time="breakfast")
        MealPlanFoodItem.objects.create(meal_plan_meal=self.meal, food_name="Rice", household_measure="1/2 cup", kcal=Decimal("100"))

    def _log_photo(self, public_id="meal-logs-private/abc"):
        self.api.force_authenticate(self.client_user)
        with mock.patch("cloudinary.uploader.upload", return_value={"public_id": public_id, "format": "jpg"}) as up:
            resp = self.api.post(f"/api/client/meals/{self.meal.id}/log/", {"photo": _jpeg()}, format="multipart")
        return resp, up

    def test_photo_is_uploaded_privately_and_links_expire(self):
        resp, up = self._log_photo()
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(up.call_args.kwargs["type"], "authenticated")  # not a public image
        log = MealLog.objects.get(pk=resp.data["id"])
        self.assertEqual((log.photo_public_id, log.photo_format, log.photo_url), ("meal-logs-private/abc", "jpg", None))

        link = resp.data["photo_url"]
        self.assertIn("api.cloudinary.com", link)  # a signed download link, not res.cloudinary.com/.../upload/
        expires = int(parse_qs(urlparse(link).query)["expires_at"][0])
        minutes = (expires - timezone.now().timestamp()) / 60
        self.assertTrue(PHOTO_LINK_MINUTES - 1 <= minutes <= PHOTO_LINK_MINUTES + 1, minutes)

        # The client's own list and the RND's view get a link; another RND gets nothing.
        self.assertTrue(self.api.get("/api/client/meal-logs/").data[0]["photo_url"].startswith("https://api.cloudinary.com"))
        self.api.force_authenticate(self.rnd)
        self.assertIn("api.cloudinary.com", self.api.get(f"/api/rnd/meal-logs/{log.id}/").data["photo_url"])
        other = approve_rnd(User.objects.create_user(email="ro@nt.ph", password="x", role="rnd", first_name="O", last_name="R"))
        self.api.force_authenticate(other)
        self.assertEqual(self.api.get(f"/api/rnd/meal-logs/{log.id}/").status_code, 404)

    def test_a_replaced_photo_is_deleted(self):
        self._log_photo("meal-logs-private/first")
        with mock.patch("cloudinary.uploader.destroy") as destroy, self.captureOnCommitCallbacks(execute=True):
            resp, _ = self._log_photo("meal-logs-private/second")
        self.assertEqual(resp.status_code, 200)
        destroy.assert_called_once()
        self.assertEqual(destroy.call_args.args[0], "meal-logs-private/first")
        self.assertEqual(destroy.call_args.kwargs["type"], "authenticated")

    def test_a_non_photo_file_is_refused(self):
        self.api.force_authenticate(self.client_user)
        bad = SimpleUploadedFile("notes.pdf", b"%PDF-1.4", content_type="application/pdf")
        with mock.patch("cloudinary.uploader.upload") as up:
            resp = self.api.post(f"/api/client/meals/{self.meal.id}/log/", {"photo": bad}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        up.assert_not_called()

    def test_moving_an_older_public_photo(self):
        from django.core.management import call_command

        old = "https://res.cloudinary.com/demo/image/upload/v1791890215/meal-logs/old_photo.jpg"
        log = MealLog.objects.create(meal_plan_meal=self.meal, client=self.client_user, log_date="2026-10-01", photo_url=old)
        self.assertEqual(public_id_from_url(old), "meal-logs/old_photo")
        with mock.patch("cloudinary.uploader.upload", return_value={"public_id": "meal-logs-private/moved", "format": "jpg"}) as up, \
                mock.patch("cloudinary.uploader.destroy") as destroy:
            call_command("make_meal_photos_private", stdout=mock.MagicMock())
        self.assertEqual(up.call_args.args[0], old)
        self.assertEqual(up.call_args.kwargs["type"], "authenticated")
        destroy.assert_called_once()
        self.assertEqual((destroy.call_args.args[0], destroy.call_args.kwargs["type"]), ("meal-logs/old_photo", "upload"))
        log.refresh_from_db()
        self.assertEqual((log.photo_public_id, log.photo_url), ("meal-logs-private/moved", None))
