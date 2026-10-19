"""Brevo HTTPS email backend (production on Render, where SMTP is blocked)."""

from unittest import mock

import httpx
from django.core.mail import EmailMultiAlternatives
from django.test import SimpleTestCase, override_settings

from .brevo_email import BrevoEmailBackend


def _ok(url, **kwargs):
    return httpx.Response(201, request=httpx.Request("POST", url), json={"messageId": "m1"})


@override_settings(FRONTEND_URL="https://nutrimatch.example", DEFAULT_FROM_EMAIL="NutriMatch <team@example.com>")
class BrevoBackendTests(SimpleTestCase):
    def _send(self, post):
        conn = BrevoEmailBackend(api_key="k", alias="test")
        msg = EmailMultiAlternatives("Hello", "Plain text", to=["Ana <ana@example.com>"], connection=conn)
        msg.attach_alternative('<img src="cid:nutrimatch-logo"><p>Hi</p>', "text/html")
        with mock.patch("core.brevo_email.httpx.post", side_effect=post) as p:
            return msg.send(), p

    def test_posts_html_text_and_links_the_logo(self):
        sent, post = self._send(_ok)
        self.assertEqual(sent, 1)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(post.call_args.kwargs["headers"]["api-key"], "k")
        self.assertEqual(payload["sender"], {"email": "team@example.com", "name": "NutriMatch"})
        self.assertEqual(payload["to"], [{"email": "ana@example.com", "name": "Ana"}])
        self.assertEqual(payload["textContent"], "Plain text")
        self.assertIn('src="https://nutrimatch.example/emails/nutrimatch-logo-96.png"', payload["htmlContent"])

    def test_api_error_raises_so_callers_see_it(self):
        def fail(url, **kwargs):
            return httpx.Response(401, request=httpx.Request("POST", url), json={"message": "Key not found"})
        with self.assertRaises(httpx.HTTPStatusError):
            self._send(fail)
