"""Run a slow side effect (an email over SMTP or Brevo takes seconds) after
the transaction commits, on a background thread, so the person's request
doesn't wait for it. Best effort, like the emails themselves: the work must
catch and log its own errors.

Under the test runner (it creates `mail.outbox`) it runs inline, so tests
can check `mail.outbox` straight after the request."""

import threading

from django.core import mail
from django.db import connection, transaction


def _inline():
    return hasattr(mail, "outbox")


def run_after_commit(work):
    def start():
        if _inline():
            work()
            return

        def run():
            try:
                work()
            finally:
                connection.close()  # this thread's own database connection

        threading.Thread(target=run, daemon=True).start()

    transaction.on_commit(start)
