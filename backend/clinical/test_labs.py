"""Lab results: the RND requests tests, the client uploads, the RND reviews.
Cloudinary is mocked — no network calls."""

import json
from datetime import timedelta
from itertools import count
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from communication.models import NotificationLog
from communication.reminders import run_due_reminders, today_items
from core.models import AuditLog
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .labs import ph_today
from .models import LabRequest, LabResult

_ids = count(1)


def fake_upload(file):
    return f"lab-results/test-{next(_ids)}", "pdf"


def pdf(name="result.pdf", size=1000):
    return SimpleUploadedFile(name, b"%PDF" + b"0" * size, content_type="application/pdf")


@patch("clinical.labs.destroy_lab_file", lambda public_id: None)
@patch("clinical.labs.fetch_lab_file", lambda result: b"%PDF-file")
@patch("clinical.labs.upload_lab_file", fake_upload)
class LabResultsTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@l.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.other_rnd = approve_rnd(User.objects.create_user(email="r2@l.ph", password="x", role="rnd", first_name="Lea", last_name="T"))
        self.c = onboard_client(User.objects.create_user(email="c@l.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active", started_at=timezone.now())
        self.appt = Appointment.objects.create(relationship=self.rel, scheduled_at=timezone.now() + timedelta(days=3),
                                               status="confirmed", type="video")
        self.rnd_api, self.client_api = APIClient(), APIClient()
        self.rnd_api.force_authenticate(self.rnd)
        self.client_api.force_authenticate(self.c)
        self.today = ph_today().isoformat()

    def request_labs(self, tests=("fbs", "hba1c"), **extra):
        return self.rnd_api.post(f"/api/rnd/relationships/{self.rel.id}/labs/", {"tests": list(tests), **extra}, format="json")

    def upload(self, tests=("fbs",), fasted="yes", request_id=None, files=None, taken_on=None):
        data = {"tests": json.dumps(list(tests)), "taken_on": taken_on or self.today, "fasted": fasted,
                "files": files or [pdf()]}
        if request_id:
            data["request_id"] = request_id
        return self.client_api.post("/api/client/labs/", data, format="multipart")

    def test_request_notifies_and_needed_before_is_next_consultation(self):
        resp = self.request_labs(note="Fast 8 hours before the glucose test.")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["needed_before"], self.appt.scheduled_at)
        self.assertEqual(resp.data["test_names"], ["Fasting blood glucose", "HbA1c"])
        note = NotificationLog.objects.get(recipient=self.c, notifiable_type="lab_request")
        self.assertIn("Fasting blood glucose, HbA1c", note.content)
        self.assertTrue(AuditLog.objects.filter(action="lab_request.created", record_id=resp.data["id"]).exists())
        # The client sees it, due before the consultation.
        data = self.client_api.get("/api/client/labs/").data
        self.assertEqual(data["requests"][0]["needed_before"], self.appt.scheduled_at)

    def test_request_rules(self):
        self.assertEqual(self.request_labs(tests=[]).status_code, 400)
        self.assertEqual(self.request_labs(tests=["xray"]).status_code, 400)
        self.assertEqual(self.request_labs(tests=["other"]).status_code, 400)  # needs the name
        self.assertEqual(self.request_labs(tests=["other"], other_tests="Vitamin D").status_code, 201)
        # Another RND can't touch this patient; a client can't request.
        other = APIClient()
        other.force_authenticate(self.other_rnd)
        self.assertEqual(other.post(f"/api/rnd/relationships/{self.rel.id}/labs/", {"tests": ["fbs"]}, format="json").status_code, 404)
        self.assertEqual(self.client_api.post(f"/api/rnd/relationships/{self.rel.id}/labs/", {"tests": ["fbs"]}, format="json").status_code, 403)
        # Discharged patients are read-only.
        self.rel.status = "discharged"
        self.rel.save()
        self.assertEqual(self.request_labs().status_code, 403)

    def test_upload_completes_request_and_rnd_reviews(self):
        req_id = self.request_labs().data["id"]
        resp = self.upload(tests=["fbs"], request_id=req_id)
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(LabRequest.objects.get(pk=req_id).status, "open")  # HbA1c still missing
        self.assertEqual(self.upload(tests=["hba1c"], fasted="na", request_id=req_id).status_code, 201)
        self.assertEqual(LabRequest.objects.get(pk=req_id).status, "completed")
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, notifiable_type="lab_result").exists())

        # The RND sees them straight away (before the consultation), marked new.
        labs = self.rnd_api.get(f"/api/rnd/relationships/{self.rel.id}/labs/").data
        self.assertEqual(len(labs["results"]), 2)
        first = labs["results"][0]
        self.assertIsNone(first["reviewed_at"])
        self.assertEqual(first["days_before_consultation"], 3)
        summary = self.rnd_api.get(f"/api/rnd/relationships/{self.rel.id}/summary/").data
        self.assertEqual(summary["labs"]["new_results"], 2)
        self.assertEqual(self.rnd_api.get("/api/rnd/dashboard/").data["todo"]["lab_results_to_review"], 2)

        # Opening the file marks it reviewed and is audit-logged; then the client can't delete it.
        resp = self.rnd_api.get(f"/api/rnd/lab-results/{first['id']}/file/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertEqual(resp["Cache-Control"], "no-store")
        self.assertIsNotNone(LabResult.objects.get(pk=first["id"]).reviewed_at)
        self.assertTrue(AuditLog.objects.filter(action="lab_result.viewed", record_id=first["id"], user=self.rnd).exists())
        self.assertEqual(self.client_api.delete(f"/api/client/lab-results/{first['id']}/").status_code, 403)

    def test_delete_before_review_reopens_request(self):
        req_id = self.request_labs(tests=["fbs"]).data["id"]
        res_id = self.upload(request_id=req_id).data["results"][0]["id"]
        self.assertEqual(LabRequest.objects.get(pk=req_id).status, "completed")
        self.assertEqual(self.client_api.delete(f"/api/client/lab-results/{res_id}/").status_code, 204)
        self.assertEqual(LabRequest.objects.get(pk=req_id).status, "open")
        self.assertTrue(AuditLog.objects.filter(action="lab_result.deleted").exists())

    def test_upload_rules(self):
        future = (ph_today() + timedelta(days=1)).isoformat()
        self.assertEqual(self.upload(taken_on=future).status_code, 400)
        self.assertEqual(self.upload(fasted="na").status_code, 400)  # glucose needs the fasting answer
        self.assertEqual(self.upload(files=[SimpleUploadedFile("x.exe", b"MZ")]).status_code, 400)
        # The contents are checked, not just the name: a Word file renamed to .pdf / .png is refused.
        docx = b"PK\x03\x04" + b"0" * 100
        self.assertEqual(self.upload(files=[SimpleUploadedFile("report.pdf", docx)]).status_code, 400)
        self.assertEqual(self.upload(files=[SimpleUploadedFile("scan.png", docx)]).status_code, 400)
        png = SimpleUploadedFile("scan.png", b"\x89PNG\r\n\x1a\n" + b"0" * 100, content_type="image/png")
        jpg = SimpleUploadedFile("photo.jpeg", b"\xff\xd8\xff\xe0" + b"0" * 100, content_type="image/jpeg")
        self.assertEqual(self.upload(files=[png, jpg]).status_code, 201)
        self.assertEqual(self.upload(files=[pdf(size=11 * 1024 * 1024)]).status_code, 400)
        self.assertEqual(self.upload(files=[pdf(f"{i}.pdf") for i in range(6)]).status_code, 400)
        # Taken before the request → upload it without the request instead.
        req_id = self.request_labs().data["id"]
        LabRequest.objects.filter(pk=req_id).update(created_at=timezone.now())
        old = (ph_today() - timedelta(days=5)).isoformat()
        self.assertEqual(self.upload(taken_on=old, request_id=req_id).status_code, 400)
        resp = self.upload(taken_on=old)
        self.assertEqual(resp.status_code, 201)
        # Flags: not fasting, older than 30 days.
        res = self.upload(fasted="no", taken_on=(ph_today() - timedelta(days=40)).isoformat()).data["results"][0]
        self.assertEqual(res["flags"], {"old": True, "not_fasting": True})

    def test_needs_an_rnd_and_privacy(self):
        res_id = self.upload().data["results"][0]["id"]
        # Another RND and another client can't open it; admins have no endpoint.
        other = APIClient()
        other.force_authenticate(self.other_rnd)
        self.assertEqual(other.get(f"/api/rnd/lab-results/{res_id}/file/").status_code, 404)
        c2 = onboard_client(User.objects.create_user(email="c2@l.ph", password="x", role="client", first_name="Ben", last_name="D"))
        api2 = APIClient()
        api2.force_authenticate(c2)
        self.assertEqual(api2.get(f"/api/client/lab-results/{res_id}/file/").status_code, 404)
        self.assertEqual(api2.post("/api/client/labs/", {"tests": json.dumps(["fbs"]), "taken_on": self.today,
                                                         "fasted": "yes", "files": [pdf()]}, format="multipart").status_code, 400)
        # The patient's own view isn't marked reviewed.
        self.assertEqual(self.client_api.get(f"/api/client/lab-results/{res_id}/file/").status_code, 200)
        self.assertIsNone(LabResult.objects.get(pk=res_id).reviewed_at)

    def test_cancel_reminder_and_my_tasks(self):
        req_id = self.request_labs().data["id"]
        # My tasks shows the open request.
        lab_items = [i for i in today_items(self.c) if i["kind"] == "lab"]
        self.assertEqual(len(lab_items), 1)
        self.assertFalse(lab_items[0]["done"])
        # The reminder goes out once, within 2 days of the consultation.
        self.assertEqual(run_due_reminders(client=self.c), 0)  # 3 days away
        later = timezone.now() + timedelta(days=1, hours=12)
        self.assertEqual(run_due_reminders(now=later, client=self.c), 1)
        self.assertEqual(run_due_reminders(now=later, client=self.c), 0)
        # Cancelling takes it off the client's list.
        self.assertEqual(self.rnd_api.delete(f"/api/rnd/lab-requests/{req_id}/").status_code, 204)
        self.assertEqual(self.client_api.get("/api/client/labs/").data["requests"], [])
        self.assertEqual([i for i in today_items(self.c) if i["kind"] == "lab"], [])
