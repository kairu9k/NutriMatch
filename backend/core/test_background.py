"""Slow side effects (emails) run after commit, off the request thread."""

import threading
from unittest.mock import patch

from django.test import TestCase

from .background import run_after_commit


class RunAfterCommitTests(TestCase):
    @patch("core.background._inline", return_value=False)  # as on a real server
    def test_runs_on_another_thread_after_commit(self, _):
        done = threading.Event()
        seen = {}

        def work():
            seen["thread"] = threading.current_thread()
            done.set()

        with self.captureOnCommitCallbacks(execute=True):
            run_after_commit(work)
            self.assertFalse(done.is_set())  # nothing before the commit
        self.assertTrue(done.wait(5))
        self.assertIsNot(seen["thread"], threading.current_thread())

    def test_runs_inline_with_the_test_outbox(self):
        seen = {}
        with self.captureOnCommitCallbacks(execute=True):
            run_after_commit(lambda: seen.setdefault("thread", threading.current_thread()))
        self.assertIs(seen["thread"], threading.current_thread())
