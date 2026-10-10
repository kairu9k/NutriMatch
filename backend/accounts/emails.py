"""Branded NutriMatch emails: HTML (templates/emails/*.html) + a plain-text
version for clients that don't show HTML. The logo is embedded as an inline
cid: image so it displays without loading anything from the internet (the
app runs on localhost in dev, which an inbox can't reach)."""

from email.message import MIMEPart
from functools import lru_cache
from pathlib import Path

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

LOGO_PATH = Path(__file__).resolve().parent / "static" / "emails" / "nutrimatch-logo-96.png"
LOGO_CID = "nutrimatch-logo"


@lru_cache(maxsize=1)
def _logo_bytes():
    try:
        return LOGO_PATH.read_bytes()
    except OSError:
        return None


def send_branded_email(*, to, subject, template, context, text, preheader=""):
    """Send one email to `to` (an address). `template` is e.g. "emails/code.html";
    `text` is the plain-text version (kept short, same content)."""
    html = render_to_string(template, {
        **context,
        "subject": subject,
        "preheader": preheader,
        "year": timezone.now().year,
    })
    message = EmailMultiAlternatives(subject=subject, body=text, to=[to])
    message.attach_alternative(html, "text/html")
    logo = _logo_bytes()
    if logo:
        part = MIMEPart()
        part.set_content(logo, maintype="image", subtype="png", disposition="inline", cid=f"<{LOGO_CID}>")
        message.attach(part)
    message.send()


def send_code_email(user, *, subject, heading, intro, code, ttl_minutes, after_code, safety_note):
    """A one-time code email (email verification, password reset)."""
    text = (
        f"Hi {user.first_name},\n\n"
        f"{intro}\n\n"
        f"Your code: {code}\n"
        f"It expires in {ttl_minutes} minutes.\n\n"
        f"{after_code}\n\n"
        f"{safety_note}\n\n"
        "Salamat,\nThe NutriMatch Team"
    )
    send_branded_email(
        to=user.email,
        subject=subject,
        template="emails/code.html",
        context={
            "first_name": user.first_name,
            "heading": heading,
            "intro": intro,
            "code": code,
            "ttl_minutes": ttl_minutes,
            "after_code": after_code,
            "safety_note": safety_note,
        },
        text=text,
        preheader=f"Your code is {code} · expires in {ttl_minutes} minutes",
    )


def send_notice_email(user, *, subject, heading, paragraphs, highlight="", button_label="", button_url="", preheader=""):
    """A general notice (e.g. RND application approved / not approved)."""
    lines = [f"Hi {user.first_name},", "", *paragraphs]
    if highlight:
        lines += ["", highlight]
    if button_url:
        lines += ["", f"{button_label}: {button_url}"]
    lines += ["", "Salamat,", "The NutriMatch Team"]
    send_branded_email(
        to=user.email,
        subject=subject,
        template="emails/notice.html",
        context={
            "first_name": user.first_name,
            "heading": heading,
            "paragraphs": paragraphs,
            "highlight": highlight,
            "button_label": button_label,
            "button_url": button_url,
        },
        text="\n".join(lines),
        preheader=preheader or (paragraphs[0] if paragraphs else ""),
    )
