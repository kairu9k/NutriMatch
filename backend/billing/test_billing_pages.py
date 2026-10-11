"""Client Billing + RND Earnings pages: what each side sees, and resends."""

from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .models import Invoice, PaymentTransaction, Payout, RndPayoutAccount


class BillingPagesTests(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox = []
        self.rnd = approve_rnd(User.objects.create_user(email="rnd@b.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.client_user = onboard_client(User.objects.create_user(email="ana@b.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        now = timezone.now()
        self.due_appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=now + timedelta(days=2))
        self.due = Invoice.objects.create(relationship=self.rel, appointment=self.due_appt, amount=Decimal("800"), commission_pct=Decimal("10"))
        done = Appointment.objects.create(relationship=self.rel, type="video", status="completed", scheduled_at=now - timedelta(days=9),
                                          completed_at=now - timedelta(days=9))
        self.paid = Invoice.objects.create(relationship=self.rel, appointment=done, amount=Decimal("800"), commission_pct=Decimal("10"),
                                           status="paid", paid_at=now - timedelta(days=10), payment_method="gcash")
        PaymentTransaction.objects.create(invoice=self.paid, transaction_type="payment", amount=Decimal("800"), status="success",
                                          gateway_payload={"data": {"id": "pay_xyz", "attributes": {"amount": 80000}}})
        self.capi = APIClient()
        self.capi.force_authenticate(self.client_user)
        self.rapi = APIClient()
        self.rapi.force_authenticate(self.rnd)

    def test_client_sees_consultation_deadline_and_receipt_but_no_commission(self):
        rows = {r["id"]: r for r in self.capi.get("/api/client/invoices/").data}
        due, paid = rows[self.due.id], rows[self.paid.id]
        self.assertEqual(due["consultation"]["rnd"]["name"], "Maria Santos")
        self.assertIsNotNone(due["pay_by"])
        self.assertIsNone(due["receipt"])
        self.assertEqual(paid["receipt"]["method"], "GCash")
        self.assertEqual(paid["receipt"]["number"], f"INV-{self.paid.id:04d}")
        self.assertNotIn("commission", str(rows).lower())

    def test_resend_receipt_once_per_two_minutes(self):
        url = f"/api/client/invoices/{self.paid.id}/resend-receipt/"
        self.assertEqual(self.capi.post(url).status_code, 200)
        self.assertEqual(mail.outbox[-1].to, ["ana@b.ph"])
        self.assertEqual(self.capi.post(url).status_code, 429)
        self.assertEqual(self.capi.post(f"/api/client/invoices/{self.due.id}/resend-receipt/").status_code, 404)  # nothing paid yet
        other = onboard_client(User.objects.create_user(email="o@b.ph", password="x", role="client", first_name="O", last_name="C"))
        oapi = APIClient()
        oapi.force_authenticate(other)
        self.assertEqual(oapi.post(url).status_code, 404)

    def test_rnd_statement_lists_every_invoice_with_its_state(self):
        data = self.rapi.get("/api/rnd/earnings/").data
        states = {r["invoice_id"]: r["state"] for r in data["statement"]}
        self.assertEqual(states, {self.due.id: "awaiting_payment", self.paid.id: "posted"})
        row = next(r for r in data["statement"] if r["invoice_id"] == self.paid.id)
        self.assertEqual((row["commission_pct"], row["share"]), (Decimal("10.00"), Decimal("720.00")))
        self.assertIsNone(data["payout_account"])

    def test_payout_detail_and_resend(self):
        RndPayoutAccount.objects.create(rnd=self.rnd, method="gcash", account_name="Maria Santos", account_number="09171234567")
        payout = Payout.objects.create(rnd=self.rnd, amount=Decimal("720"), payout_date=timezone.localdate(), method="gcash",
                                       account_name="Maria Santos", account_number="09171234567", reference="GC-1", released_at=timezone.now())
        Invoice.objects.filter(pk=self.paid.pk).update(payout=payout)
        detail = self.rapi.get(f"/api/rnd/payouts/{payout.id}/").data
        self.assertEqual([i["invoice_id"] for i in detail["invoices"]], [self.paid.id])
        self.assertEqual(self.rapi.get("/api/rnd/earnings/").data["payout_account"]["account_number_last4"], "4567")
        resp = self.rapi.post(f"/api/rnd/payouts/{payout.id}/resend/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("₱720.00", mail.outbox[-1].subject)
        self.assertEqual(self.rapi.post(f"/api/rnd/payouts/{payout.id}/resend/").status_code, 429)
        other = approve_rnd(User.objects.create_user(email="x@b.ph", password="x", role="rnd", first_name="X", last_name="Y"))
        xapi = APIClient()
        xapi.force_authenticate(other)
        self.assertEqual(xapi.get(f"/api/rnd/payouts/{payout.id}/").status_code, 404)
