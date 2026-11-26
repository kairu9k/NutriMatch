"""After the defense: take every demo-mode payment (scheduling/demo.py) out of the money.

Each invoice paid in demo mode carries DEMO_PAYMENT_NOTE. This marks those invoices cancelled
(void), so they leave Billing totals, Platform Reports and the RNDs' earnings and payouts. The
consultations themselves stay in everyone's history. An invoice already paid out to an RND is
only reported, never changed (that money was recorded as sent).

    python manage.py clear_demo_payments --dry-run   # list what would change
    python manage.py clear_demo_payments
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import AuditLog
from scheduling.demo import DEMO_PAYMENT_NOTE

from ...models import Invoice

VOIDED_NOTE = "Voided after the demo (clear_demo_payments)."


class Command(BaseCommand):
    help = "Void the invoices paid in demo mode, so they leave the money totals and RND payouts."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only list what would change.")

    def handle(self, *args, dry_run=False, **options):
        demo = Invoice.objects.filter(notes__contains=DEMO_PAYMENT_NOTE).exclude(status=Invoice.Status.CANCELLED)
        paid_out = list(demo.filter(payout__isnull=False))
        to_void = list(demo.filter(payout__isnull=True).select_related("relationship__client", "relationship__rnd"))

        for inv in paid_out:
            self.stdout.write(self.style.WARNING(f"INV-{inv.id:04d} was already paid out to the RND; left as it is."))
        for inv in to_void:
            self.stdout.write(f"INV-{inv.id:04d}  {inv.relationship.client.email} -> RND {inv.relationship.rnd.email}  "
                              f"PHP {inv.amount}  ({inv.status})")
        if not to_void:
            self.stdout.write("No demo payments to clear.")
            return
        if dry_run:
            self.stdout.write(f"Dry run: {len(to_void)} invoice(s) would be voided.")
            return

        with transaction.atomic():
            for inv in to_void:
                old = inv.status
                inv.status = Invoice.Status.CANCELLED
                inv.notes = f"{inv.notes}\n{VOIDED_NOTE}"
                inv.save(update_fields=["status", "notes"])
                AuditLog.objects.create(action="invoice.demo_voided", table_name="invoices", record_id=inv.id,
                                        old_values={"status": old}, new_values={"status": Invoice.Status.CANCELLED})
        self.stdout.write(self.style.SUCCESS(f"Voided {len(to_void)} demo invoice(s)."))
