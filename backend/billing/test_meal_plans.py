"""Paid meal plans (2026-11-04): consultation only vs consultation + meal
plan, the add-on after a consultation, one payment = one sent plan, and sent
plans are locked."""

from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, booking_slot, onboard_client
from nutrition.models import MealPlan, MealPlanFoodItem, MealPlanMeal
from scheduling.models import Appointment, RndClientRelationship

from .meal_plans import OFFER_DAYS, create_offer, expire_offers, unused_credit
from .models import Invoice
from .payouts import HOLD_DAYS, invoice_state
from .services import create_appointment_invoice, record_successful_payment


def _rnd(email="rnd@mp.ph", meal_plan_fee=Decimal("1500.00")):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="Rita", last_name="Diaz")
    return approve_rnd(user, consultation_fee=Decimal("800.00"), meal_plan_fee=meal_plan_fee)


def _client(email="client@mp.ph"):
    user = User.objects.create_user(email=email, password="x", role="client", first_name="Carl", last_name="Lim")
    return onboard_client(user)


def _pay(invoice):
    with mock.patch("billing.receipts.send_payment_receipts"):
        record_successful_payment(invoice, "pay_test", {}, "test")
    invoice.refresh_from_db()
    return invoice


def _plan(rel, name="Plan"):
    plan = MealPlan.objects.create(relationship=rel, name=name)
    meal = MealPlanMeal.objects.create(meal_plan=plan, day_of_week=1, meal_time="breakfast")
    MealPlanFoodItem.objects.create(meal_plan_meal=meal, food_name="Rice")
    return plan


class PriceRulesTests(TestCase):
    def test_package_must_cost_at_least_100_more(self):
        rnd = _rnd(meal_plan_fee=None)
        api = APIClient()
        api.force_authenticate(rnd)
        resp = api.patch("/api/rnd/profile/", {"meal_plan_fee": "850.00"}, format="json")
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("meal_plan_fee", resp.data)
        resp = api.patch("/api/rnd/profile/", {"meal_plan_fee": "900.00"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        resp = api.patch("/api/rnd/profile/", {"meal_plan_fee": None}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)


class BookingTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.client_user = _client()
        self.api.force_authenticate(self.client_user)

    def _book(self, rnd, service):
        return self.api.post("/api/client/appointments/", {
            "rnd_id": rnd.id, "service": service, "scheduled_at": booking_slot(2).isoformat(),
            "type": "video", "duration_minutes": 60,
        }, format="json")

    def test_package_refused_when_the_rnd_offers_no_meal_plans(self):
        rnd = _rnd(meal_plan_fee=None)
        resp = self._book(rnd, "consultation_meal_plan")
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("service", resp.data)

    def test_package_is_billed_at_the_package_price(self):
        rnd = _rnd()
        resp = self._book(rnd, "consultation_meal_plan")
        self.assertEqual(resp.status_code, 201, resp.data)
        appt = Appointment.objects.get(pk=resp.data["id"])
        self.assertEqual(appt.service, "consultation_meal_plan")
        invoice, _ = create_appointment_invoice(appt)
        self.assertEqual(invoice.kind, Invoice.Kind.PACKAGE)
        self.assertEqual(invoice.amount, Decimal("1500.00"))

    def test_consultation_only_is_billed_at_the_consultation_fee(self):
        rnd = _rnd()
        resp = self._book(rnd, "consultation")
        appt = Appointment.objects.get(pk=resp.data["id"])
        invoice, _ = create_appointment_invoice(appt)
        self.assertEqual(invoice.kind, Invoice.Kind.CONSULTATION)
        self.assertEqual(invoice.amount, Decimal("800.00"))


class SendAndLockTests(TestCase):
    def setUp(self):
        self.rnd = _rnd()
        self.client_user = _client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)

    def _send(self, plan):
        return self.api.post(f"/api/rnd/meal-plans/{plan.id}/send/")

    def _paid_package(self):
        appt = Appointment.objects.create(relationship=self.rel, scheduled_at=timezone.now() - timedelta(days=1),
                                          status="completed", service="consultation_meal_plan")
        invoice, _ = create_appointment_invoice(appt)
        return _pay(invoice)

    def test_send_needs_a_paid_meal_plan(self):
        plan = _plan(self.rel)
        resp = self._send(plan)
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(resp.data["code"], "no_credit")

    def test_one_payment_sends_one_plan(self):
        invoice = self._paid_package()
        plan = _plan(self.rel)
        self.assertEqual(self._send(plan).status_code, 200)
        plan.refresh_from_db()
        self.assertEqual(plan.invoice_id, invoice.id)
        self.assertIsNone(unused_credit(self.rel))
        second = _plan(self.rel, "Second")
        self.assertEqual(self._send(second).status_code, 400)

    def test_sent_plan_is_locked_and_can_be_copied(self):
        self._paid_package()
        plan = _plan(self.rel)
        self._send(plan)
        week = self.api.put(f"/api/rnd/meal-plans/{plan.id}/week/", {"meals": []}, format="json")
        self.assertEqual(week.status_code, 403)
        edit = self.api.patch(f"/api/rnd/meal-plans/{plan.id}/", {"name": "New name"}, format="json")
        self.assertEqual(edit.status_code, 403)
        again = self._send(plan)
        self.assertEqual(again.status_code, 400)
        copy = self.api.post(f"/api/rnd/meal-plans/{plan.id}/copy/")
        self.assertEqual(copy.status_code, 201, copy.data)
        draft = MealPlan.objects.get(pk=copy.data["id"])
        self.assertEqual(draft.status, "draft")
        self.assertEqual(draft.meals.get().food_items.get().food_name, "Rice")
        # drafts stay editable
        self.assertEqual(self.api.patch(f"/api/rnd/meal-plans/{draft.id}/", {"name": "Week 2"}, format="json").status_code, 200)


class AddOnTests(TestCase):
    def setUp(self):
        self.rnd = _rnd()
        self.client_user = _client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

    def test_offer_is_the_difference_and_one_at_a_time(self):
        offer = create_offer(self.rel, self.rnd, "For your blood sugar")
        self.assertEqual(offer.kind, Invoice.Kind.MEAL_PLAN_ADDON)
        self.assertEqual(offer.amount, Decimal("700.00"))
        self.assertIsNone(offer.appointment_id)
        self.assertEqual(offer.commission_amt, Decimal("70.00"))
        with self.assertRaises(Exception):
            create_offer(self.rel, self.rnd)

    def test_client_can_decline(self):
        offer = create_offer(self.rel, self.rnd)
        api = APIClient()
        api.force_authenticate(self.client_user)
        resp = api.post(f"/api/client/invoices/{offer.id}/decline-offer/")
        self.assertEqual(resp.status_code, 200, resp.data)
        offer.refresh_from_db()
        self.assertEqual(offer.status, Invoice.Status.CANCELLED)

    def test_offer_expires_after_seven_days(self):
        offer = create_offer(self.rel, self.rnd)
        Invoice.objects.filter(pk=offer.pk).update(created_at=timezone.now() - timedelta(days=OFFER_DAYS, minutes=1))
        self.assertEqual(expire_offers(), 1)
        offer.refresh_from_db()
        self.assertEqual(offer.status, Invoice.Status.CANCELLED)

    def test_paid_addon_is_a_credit_and_its_share_posts_after_the_plan_is_sent(self):
        offer = _pay(create_offer(self.rel, self.rnd))
        self.assertEqual(unused_credit(self.rel), offer)
        self.assertEqual(invoice_state(offer), "pending")
        api = APIClient()
        api.force_authenticate(self.rnd)
        plan = _plan(self.rel)
        self.assertEqual(api.post(f"/api/rnd/meal-plans/{plan.id}/send/").status_code, 200)
        offer.refresh_from_db()
        self.assertEqual(invoice_state(offer), "pending")
        later = timezone.now() + timedelta(days=HOLD_DAYS, minutes=1)
        self.assertEqual(invoice_state(offer, later), "posted")

    def test_discharge_refunds_a_paid_addon_whose_plan_was_never_sent(self):
        from scheduling.discharge import discharge

        offer = _pay(create_offer(self.rel, self.rnd))
        discharge(self.rel, self.rnd, "Goals reached, care complete.")
        offer.refresh_from_db()
        self.assertEqual(offer.status, Invoice.Status.REFUND_PENDING)

    def test_payment_after_the_offer_ended_is_flagged_for_refund(self):
        offer = create_offer(self.rel, self.rnd)
        Invoice.objects.filter(pk=offer.pk).update(status=Invoice.Status.CANCELLED)
        offer.refresh_from_db()
        offer = _pay(offer)
        self.assertEqual(offer.status, Invoice.Status.REFUND_PENDING)
