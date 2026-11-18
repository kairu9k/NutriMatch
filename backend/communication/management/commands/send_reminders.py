"""Send every reminder that's due (the proposal's ReminderScheduler), and close ended video consultations.

    python manage.py send_reminders            # once (e.g. from cron / Task Scheduler every 5 minutes)
    python manage.py send_reminders --loop 300 # keep running, every 5 minutes (dev)
"""
import time

from django.core.management.base import BaseCommand

from communication.reminders import run_due_reminders
from scheduling.closing import auto_close_due


class Command(BaseCommand):
    help = "Send due reminders (appointments, payments, meal logging, RND reminders)."

    def add_arguments(self, parser):
        parser.add_argument("--loop", type=int, default=0, help="Repeat every N seconds instead of running once.")

    def handle(self, *args, **options):
        while True:
            sent = run_due_reminders()
            self.stdout.write(f"Sent {sent} reminder{'' if sent == 1 else 's'}.")
            closed = auto_close_due()  # ended video consultations close from the call record, without anyone opening the app
            self.stdout.write(f"Closed {closed} consultation{'' if closed == 1 else 's'}.")
            if not options["loop"]:
                return
            time.sleep(options["loop"])
