"""Lab results (added after the proposal, 2026-10-16, user's design).

The RND requests lab tests from the patient's chart; the patient uploads the
results (photo or PDF) before their next consultation; the RND opens them —
which marks them reviewed — and types the values into the NCP form. Nothing
is read out of the files automatically.

Privacy (RA 10173): files are *authenticated* Cloudinary assets that are never
handed out as links — the API fetches the file and streams it to the patient
or their treating RND only. Admins have no access. Every RND view writes a
`lab_result.viewed` audit row; requests, uploads and deletions are logged too.
A missing lab never blocks a consultation, completion or finalizing an NCP.
"""

import logging
import os
from datetime import timedelta

import httpx
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from core.models import AuditLog
from scheduling.discharge import ensure_open
from scheduling.models import Appointment, RndClientRelationship

from .models import LabRequest, LabResult

logger = logging.getLogger(__name__)

# Order = the order shown in the request form. "other" needs typed text.
LAB_TESTS = [
    ("fbs", "Fasting blood glucose"),
    ("hba1c", "HbA1c"),
    ("lipid", "Lipid profile"),
    ("creatinine", "Creatinine / eGFR"),
    ("bun", "BUN"),
    ("uric_acid", "Uric acid"),
    ("cbc", "CBC"),
    ("urinalysis", "Urinalysis"),
    ("alt", "SGPT / ALT"),
    ("other", "Other"),
]
LAB_TEST_NAMES = dict(LAB_TESTS)

ALLOWED_EXTENSIONS = {".pdf": "pdf", ".jpg": "jpg", ".jpeg": "jpg", ".png": "png"}
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES_PER_UPLOAD = 5
MAX_UPLOADS_PER_DAY = 20
MAX_NOTE = 500
CURRENT_DAYS = 30  # a result taken longer than this before the consultation is flagged
CLOUDINARY_FOLDER = "lab-results"


def ph_today():
    from scheduling.serializers import PH_TZ

    return timezone.now().astimezone(PH_TZ).date()


def ph_date(dt):
    from scheduling.serializers import PH_TZ

    return dt.astimezone(PH_TZ).date()


def test_names(codes, other=""):
    names = [LAB_TEST_NAMES.get(c, c) for c in codes if c != "other"]
    if "other" in codes and other:
        names.append(other)
    return names


def next_consultation(relationship, now=None):
    """The patient's next booked (pending or confirmed) consultation with this RND."""
    now = now or timezone.now()
    return (relationship.appointments
            .filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED], scheduled_at__gt=now)
            .order_by("scheduled_at").first())


# --------------------------------------------------------------- Cloudinary
class LabFileError(Exception):
    pass


def _configure():
    import cloudinary

    cfg = settings.CLOUDINARY
    if not (cfg["CLOUD_NAME"] and cfg["API_KEY"] and cfg["API_SECRET"]):
        raise LabFileError("File storage isn't set up yet (Cloudinary keys missing in .env).")
    cloudinary.config(cloud_name=cfg["CLOUD_NAME"], api_key=cfg["API_KEY"], api_secret=cfg["API_SECRET"], secure=True)


def upload_lab_file(file):
    """Stores the file as an authenticated (non-public) asset. Returns (public_id, format)."""
    import cloudinary.exceptions
    import cloudinary.uploader

    _configure()
    try:
        result = cloudinary.uploader.upload(file, folder=CLOUDINARY_FOLDER, resource_type="image", type="authenticated")
    except cloudinary.exceptions.Error as exc:
        raise LabFileError(f"Could not upload the file: {exc}") from exc
    return result["public_id"], result.get("format") or ""


def fetch_lab_file(result):
    """The file's bytes, fetched server-side through Cloudinary's API with a
    one-minute download link — the link itself never reaches the browser."""
    import cloudinary.utils

    _configure()
    url = cloudinary.utils.private_download_url(
        result.file_public_id, result.file_format, resource_type="image", type="authenticated",
        expires_at=int((timezone.now() + timedelta(minutes=1)).timestamp()),
    )
    try:
        resp = httpx.get(url, timeout=20, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise LabFileError("Could not load the file. Please try again.") from exc
    return resp.content


def destroy_lab_file(public_id):
    """Best effort — a failed delete leaves an orphan asset, never an error."""
    try:
        import cloudinary.uploader

        _configure()
        cloudinary.uploader.destroy(public_id, resource_type="image", type="authenticated", invalidate=True)
    except Exception:
        logger.exception("Could not delete lab file %s", public_id)


CONTENT_TYPES = {"pdf": "application/pdf", "jpg": "image/jpeg", "png": "image/png"}


def file_response(result):
    try:
        data = fetch_lab_file(result)
    except LabFileError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    resp = HttpResponse(data, content_type=CONTENT_TYPES.get(result.file_format, "application/octet-stream"))
    safe_name = result.file_name.replace('"', "")
    resp["Content-Disposition"] = f'inline; filename="{safe_name}"'
    resp["Cache-Control"] = "no-store"
    return resp


def audit(request, action, obj, new_values=None):
    AuditLog.objects.create(
        user=request.user, action=action, table_name=obj._meta.db_table, record_id=obj.pk,
        new_values=new_values, ip_address=request.META.get("REMOTE_ADDR"),
    )


# --------------------------------------------------------------- payloads
def request_payload(req, now=None):
    nxt = next_consultation(req.relationship, now) if req.status == LabRequest.Status.OPEN else None
    covered = set()
    for r in req.results.all():
        covered.update(r.tests)
    return {
        "id": req.id,
        "relationship_id": req.relationship_id,
        "tests": req.tests,
        "other_tests": req.other_tests,
        "test_names": test_names(req.tests, req.other_tests),
        "uploaded_tests": [t for t in req.tests if t in covered],
        "note": req.note,
        "status": req.status,
        "created_at": req.created_at,
        "completed_at": req.completed_at,
        "requested_by": req.requested_by.full_name if req.requested_by else None,
        # "needed before" = the next booked consultation (null: none booked yet)
        "needed_before": nxt.scheduled_at if nxt else None,
    }


def result_payload(res, now=None):
    now = now or timezone.now()
    # How long before the consultation it was taken: the first consultation
    # on/after the test date (upcoming, or already held).
    appt = (res.relationship.appointments
            .filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED],
                    scheduled_at__date__gte=res.taken_on)
            .order_by("scheduled_at").first())
    days_before = (ph_date(appt.scheduled_at) - res.taken_on).days if appt else None
    age = days_before if days_before is not None else (ph_today() - res.taken_on).days
    return {
        "id": res.id,
        "relationship_id": res.relationship_id,
        "request_id": res.request_id,
        "tests": res.tests,
        "other_tests": res.other_tests,
        "test_names": test_names(res.tests, res.other_tests),
        "taken_on": res.taken_on,
        "fasted": res.fasted,
        "file_name": res.file_name,
        "file_format": res.file_format,
        "file_size": res.file_size,
        "uploaded_at": res.uploaded_at,
        "reviewed_at": res.reviewed_at,
        "declined_at": res.declined_at,
        "decline_reason": res.decline_reason,
        "consultation_at": appt.scheduled_at if appt else None,
        "days_before_consultation": days_before,
        "flags": {
            "old": age > CURRENT_DAYS,
            "not_fasting": res.fasted == LabResult.Fasted.NO and "fbs" in res.tests,
        },
    }


def refresh_request_status(req):
    """A request is completed once every requested test has an upload (and
    reopens if an unreviewed upload is deleted or the RND declines one)."""
    if req.status == LabRequest.Status.CANCELLED:
        return
    covered = set()
    for r in req.results.filter(declined_at__isnull=True):
        covered.update(r.tests)
    done = set(req.tests) <= covered
    if done and req.status == LabRequest.Status.OPEN:
        req.status, req.completed_at = LabRequest.Status.COMPLETED, timezone.now()
        req.save(update_fields=["status", "completed_at"])
    elif not done and req.status == LabRequest.Status.COMPLETED:
        req.status, req.completed_at = LabRequest.Status.OPEN, None
        req.save(update_fields=["status", "completed_at"])


# --------------------------------------------------------------- validation
def clean_tests(codes, other):
    if not isinstance(codes, list) or not codes:
        raise ValidationError({"tests": "Pick at least one test."})
    unknown = [c for c in codes if c not in LAB_TEST_NAMES]
    if unknown:
        raise ValidationError({"tests": "Unknown test."})
    codes = [c for c, _ in LAB_TESTS if c in codes]  # de-duplicate, keep the form's order
    other = (other or "").strip()
    if "other" in codes and not other:
        raise ValidationError({"other_tests": "Type the other test's name."})
    if len(other) > 200:
        raise ValidationError({"other_tests": "Keep it under 200 characters."})
    return codes, (other if "other" in codes else "")


class LabRequestCreateSerializer(serializers.Serializer):
    tests = serializers.ListField(child=serializers.CharField())
    other_tests = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="", max_length=MAX_NOTE)

    def validate(self, attrs):
        attrs["tests"], attrs["other_tests"] = clean_tests(attrs["tests"], attrs["other_tests"])
        attrs["note"] = attrs["note"].strip()
        return attrs


class LabUploadSerializer(serializers.Serializer):
    tests = serializers.JSONField()  # a JSON list in the multipart form
    other_tests = serializers.CharField(required=False, allow_blank=True, default="")
    taken_on = serializers.DateField()
    fasted = serializers.ChoiceField(choices=LabResult.Fasted.choices, required=False, default=LabResult.Fasted.NA)
    request_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        attrs["tests"], attrs["other_tests"] = clean_tests(attrs["tests"], attrs["other_tests"])
        if attrs["taken_on"] > ph_today():
            raise ValidationError({"taken_on": "The test date can't be in the future."})
        if "fbs" in attrs["tests"] and attrs["fasted"] == LabResult.Fasted.NA:
            raise ValidationError({"fasted": "Say whether you fasted before the glucose test."})
        return attrs


def sniff_format(f):
    """What the file really is, from its first bytes — the name can lie
    (a Word file renamed to .pdf). Returns pdf / jpg / png or None."""
    head = f.read(8)
    f.seek(0)
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    return None


def clean_files(files):
    if not files:
        raise ValidationError({"files": "Choose a file to upload."})
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise ValidationError({"files": f"Upload up to {MAX_FILES_PER_UPLOAD} files at a time."})
    out = []
    for f in files:
        ext = os.path.splitext(f.name or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS or sniff_format(f) != ALLOWED_EXTENSIONS[ext]:
            raise ValidationError({"files": f"{f.name}: only PDF, JPG or PNG files."})
        if f.size > MAX_FILE_BYTES:
            raise ValidationError({"files": f"{f.name}: the file is larger than 10 MB."})
        out.append((f, ALLOWED_EXTENSIONS[ext]))
    return out


# --------------------------------------------------------------- RND views
def _rnd_relationship(request, relationship_id):
    return get_object_or_404(RndClientRelationship.objects.select_related("client"), pk=relationship_id, rnd=request.user)


class RndLabsView(APIView):
    """GET the patient's lab requests + results; POST a new request."""

    permission_classes = [IsRnd]

    def get(self, request, relationship_id):
        rel = _rnd_relationship(request, relationship_id)
        now = timezone.now()
        reqs = rel.lab_requests.select_related("requested_by", "relationship").prefetch_related("results")
        results = rel.lab_results.select_related("relationship")
        nxt = next_consultation(rel, now)
        return Response({
            "tests": [{"code": c, "name": n} for c, n in LAB_TESTS],
            "can_request": rel.status == RndClientRelationship.Status.ACTIVE,
            "next_consultation": nxt.scheduled_at if nxt else None,
            "requests": [request_payload(r, now) for r in reqs],
            "results": [result_payload(r, now) for r in results],
        })

    def post(self, request, relationship_id):
        rel = _rnd_relationship(request, relationship_id)
        ensure_open(rel)
        if rel.status != RndClientRelationship.Status.ACTIVE:
            raise PermissionDenied("Lab tests can be requested once the patient is active (after you confirm their booking).")
        ser = LabRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        req = LabRequest.objects.create(relationship=rel, requested_by=request.user, **ser.validated_data)
        audit(request, "lab_request.created", req, {"tests": req.tests})

        from communication.services import notify

        names = ", ".join(test_names(req.tests, req.other_tests))
        nxt = next_consultation(rel)
        when = ""
        if nxt:
            from scheduling.views import format_ph_datetime

            when = f" Please upload the results before your consultation on {format_ph_datetime(nxt.scheduled_at)}."
        notify(rel.client, "lab_request", req.id, "Your RND requested lab tests",
               f"RND {request.user.full_name} requested: {names}.{when}")
        return Response(request_payload(req), status=status.HTTP_201_CREATED)


class RndLabRequestCancelView(APIView):
    permission_classes = [IsRnd]

    def delete(self, request, pk):
        req = get_object_or_404(LabRequest, pk=pk, relationship__rnd=request.user)
        ensure_open(req.relationship)
        if req.status != LabRequest.Status.OPEN:
            raise ValidationError({"detail": "Only an open request can be cancelled."})
        req.status, req.cancelled_at = LabRequest.Status.CANCELLED, timezone.now()
        req.save(update_fields=["status", "cancelled_at"])
        audit(request, "lab_request.cancelled", req)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RndLabFileView(APIView):
    """Streams the file to the treating RND and records every view (RA 10173).
    Opening it doesn't accept it: the RND presses Accept or Decline
    (RndLabResultReviewView). Discharged patients stay viewable."""

    permission_classes = [IsRnd]

    def get(self, request, pk):
        res = get_object_or_404(LabResult.objects.select_related("relationship"), pk=pk, relationship__rnd=request.user)
        audit(request, "lab_result.viewed", res)
        return file_response(res)


class RndLabResultReviewView(APIView):
    """POST {action: accept} marks the result reviewed (final for the client);
    {action: decline, reason ≥ 10} sends it back so the client uploads it
    again (the client is notified and the request reopens). An accepted
    result can't be declined later."""

    permission_classes = [IsRnd]

    def post(self, request, pk):
        from communication.services import notify

        res = get_object_or_404(LabResult.objects.select_related("relationship__client", "request"), pk=pk, relationship__rnd=request.user)
        if res.reviewed_at:
            raise ValidationError({"detail": "You already accepted this result."})
        action = (request.data.get("action") or "").strip()
        names = ", ".join(test_names(res.tests, res.other_tests))
        if action == "accept":
            res.reviewed_at, res.reviewed_by = timezone.now(), request.user
            res.declined_at, res.decline_reason = None, ""
            res.save(update_fields=["reviewed_at", "reviewed_by", "declined_at", "decline_reason"])
            audit(request, "lab_result.accepted", res)
            notify(res.relationship.client, "lab_result", res.id, "Lab result accepted",
                   f"RND {request.user.full_name} accepted your lab result: {names}.")
        elif action == "decline":
            reason = (request.data.get("reason") or "").strip()
            if len(reason) < 10:
                raise ValidationError({"reason": "Tell the patient why, in at least 10 characters."})
            res.declined_at, res.decline_reason = timezone.now(), reason[:500]
            res.save(update_fields=["declined_at", "decline_reason"])
            audit(request, "lab_result.declined", res, {"reason": reason[:500]})
            if res.request:
                refresh_request_status(res.request)
            notify(res.relationship.client, "lab_result", res.id, "Please upload your lab result again",
                   f"RND {request.user.full_name} couldn't use your lab result ({names}): {reason[:500]}")
        else:
            raise ValidationError({"action": "Use accept or decline."})
        return Response(result_payload(res))


# --------------------------------------------------------------- client views
def _client_relationship(client):
    """Uploads go to the client's current RND (an active relationship)."""
    return (RndClientRelationship.objects.filter(client=client, status=RndClientRelationship.Status.ACTIVE)
            .select_related("rnd").order_by("-started_at", "-id").first())


class ClientLabsView(APIView):
    """GET the client's requests + results; POST (multipart) an upload."""

    permission_classes = [IsClient]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        now = timezone.now()
        rel = _client_relationship(request.user)
        reqs = (LabRequest.objects.filter(relationship__client=request.user)
                .exclude(status=LabRequest.Status.CANCELLED)
                .select_related("requested_by", "relationship").prefetch_related("results"))
        results = LabResult.objects.filter(relationship__client=request.user).select_related("relationship")
        nxt = next_consultation(rel, now) if rel else None
        return Response({
            "tests": [{"code": c, "name": n} for c, n in LAB_TESTS],
            "has_rnd": rel is not None,
            "rnd_name": rel.rnd.full_name if rel else None,
            "next_consultation": nxt.scheduled_at if nxt else None,
            "requests": [request_payload(r, now) for r in reqs],
            "results": [result_payload(r, now) for r in results],
        })

    def post(self, request):
        rel = _client_relationship(request.user)
        if rel is None:
            raise ValidationError({"detail": "You can upload lab results once you have an RND."})
        ser = LabUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        files = clean_files(request.FILES.getlist("files"))

        req = None
        if data.get("request_id"):
            req = LabRequest.objects.filter(pk=data["request_id"], relationship=rel).first()
            if req is None or req.status == LabRequest.Status.CANCELLED:
                raise ValidationError({"request_id": "That request is no longer open."})
            if data["taken_on"] < ph_date(req.created_at):
                raise ValidationError({"taken_on": "This test was taken before your RND's request — upload it without choosing the request."})

        since = timezone.now() - timedelta(days=1)
        if LabResult.objects.filter(uploaded_by=request.user, uploaded_at__gte=since).count() + len(files) > MAX_UPLOADS_PER_DAY:
            raise ValidationError({"files": "You've reached today's upload limit. Please try again tomorrow."})

        created = []
        try:
            for f, fmt in files:
                public_id, stored_fmt = upload_lab_file(f)
                created.append(LabResult.objects.create(
                    relationship=rel, request=req, tests=data["tests"], other_tests=data["other_tests"],
                    taken_on=data["taken_on"], fasted=data["fasted"], file_public_id=public_id,
                    file_format=stored_fmt or fmt, file_name=(f.name or "lab-result")[:255], file_size=f.size,
                    uploaded_by=request.user,
                ))
        except LabFileError as exc:
            for r in created:  # all or nothing
                destroy_lab_file(r.file_public_id)
                r.delete()
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        for r in created:
            audit(request, "lab_result.uploaded", r, {"tests": r.tests, "taken_on": r.taken_on.isoformat()})
        if req:
            refresh_request_status(req)

        from communication.services import notify

        names = ", ".join(test_names(data["tests"], data["other_tests"]))
        notify(rel.rnd, "lab_result", created[0].id, "Lab results uploaded",
               f"{request.user.full_name} uploaded lab results: {names}.")
        now = timezone.now()
        return Response({"results": [result_payload(r, now) for r in created]}, status=status.HTTP_201_CREATED)


class ClientLabResultView(APIView):
    """DELETE an upload (only before the RND has reviewed it)."""

    permission_classes = [IsClient]

    def delete(self, request, pk):
        res = get_object_or_404(LabResult, pk=pk, relationship__client=request.user)
        if res.reviewed_at:
            raise PermissionDenied("Your RND has already reviewed this result, so it can't be removed.")
        req, public_id = res.request, res.file_public_id
        audit(request, "lab_result.deleted", res, {"tests": res.tests})
        res.delete()
        if req:
            refresh_request_status(req)
        transaction.on_commit(lambda: destroy_lab_file(public_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientLabFileView(APIView):
    permission_classes = [IsClient]

    def get(self, request, pk):
        res = get_object_or_404(LabResult, pk=pk, relationship__client=request.user)
        return file_response(res)


# --------------------------------------------------------------- summaries
def rnd_lab_counts(relationship):
    """For the chart / room / dashboards: open requests and unreviewed uploads."""
    return {
        "open_requests": relationship.lab_requests.filter(status=LabRequest.Status.OPEN).count(),
        "new_results": relationship.lab_results.filter(reviewed_at__isnull=True, declined_at__isnull=True).count(),
        "total_results": relationship.lab_results.count(),
    }
