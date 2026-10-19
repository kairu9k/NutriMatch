"""Email through Brevo's HTTPS API (https://brevo.com, free: 300 emails/day).

Render's free web services block outgoing SMTP (ports 25/465/587), so Gmail
SMTP can't connect from production and every email request hangs. Brevo's
API goes over HTTPS (port 443). Used when BREVO_API_KEY is set (settings
MAILERS); locally Gmail SMTP / the console still work as before.

The sender (DEFAULT_FROM_EMAIL) must be a verified sender in Brevo. Inline
cid: images can't be sent through the API, so the email logo is linked from
the frontend instead (FRONTEND_URL/emails/...).
"""

import base64
import logging
from email.utils import parseaddr

import httpx
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

API_URL = "https://api.brevo.com/v3/smtp/email"
LOGO_URL_PATH = "/emails/nutrimatch-logo-96.png"  # frontend/public/emails/


def _contact(address):
    name, email = parseaddr(address)
    return {"email": email, **({"name": name} if name else {})}


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, *, api_key="", timeout=20, **kwargs):
        super().__init__(**kwargs)
        self.fail_silently = fail_silently
        self.api_key = api_key
        self.timeout = timeout

    def _payload(self, message):
        html = next((content for content, mimetype in getattr(message, "alternatives", []) if mimetype == "text/html"), None)
        if html:
            html = html.replace("cid:nutrimatch-logo", settings.FRONTEND_URL + LOGO_URL_PATH)
        payload = {
            "sender": _contact(message.from_email or settings.DEFAULT_FROM_EMAIL),
            "to": [_contact(a) for a in message.to],
            "subject": message.subject,
            "textContent": message.body or " ",
        }
        if html:
            payload["htmlContent"] = html
        if message.cc:
            payload["cc"] = [_contact(a) for a in message.cc]
        if message.bcc:
            payload["bcc"] = [_contact(a) for a in message.bcc]
        if message.reply_to:
            payload["replyTo"] = _contact(message.reply_to[0])
        files = []
        for att in message.attachments:
            # (filename, content, mimetype) tuples; inline MIME parts (the
            # cid logo) are skipped — the logo is linked instead.
            if isinstance(att, tuple) and att[0]:
                content = att[1].encode() if isinstance(att[1], str) else att[1]
                files.append({"name": att[0], "content": base64.b64encode(content).decode()})
        if files:
            payload["attachment"] = files
        return payload

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            if not message.to and not message.cc and not message.bcc:
                continue
            try:
                resp = httpx.post(API_URL, json=self._payload(message), timeout=self.timeout,
                                  headers={"api-key": self.api_key, "accept": "application/json"})
                resp.raise_for_status()
                sent += 1
            except Exception:
                logger.exception("Brevo could not send the email %r", message.subject)
                if not self.fail_silently:
                    raise
        return sent
