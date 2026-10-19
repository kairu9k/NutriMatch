"""SMS through Semaphore (Philippine SMS gateway, https://semaphore.co).

Only this file knows the provider, so switching later is a change here.
Texts are short (one 160-character SMS = one credit) and never carry health
details (RA 10173): just what's due and a nudge to open the app.

With SEMAPHORE_API_KEY blank (dev/tests) nothing is sent — the text is only
logged, like the console email backend. A failed send is logged and skipped;
it never breaks the reminder that triggered it.
"""

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

SEMAPHORE_URL = "https://api.semaphore.co/api/v4/messages"
MAX_LENGTH = 160  # one SMS segment = one Semaphore credit


def normalize_ph_mobile(raw):
    """'0917 123 4567', '+63 917 123 4567' or '639171234567' -> '09171234567';
    None when it isn't a Philippine mobile number."""
    import phonenumbers

    try:
        number = phonenumbers.parse((raw or "").strip(), "PH")
    except phonenumbers.NumberParseException:
        return None
    if (phonenumbers.region_code_for_number(number) != "PH" or not phonenumbers.is_valid_number(number)
            or phonenumbers.number_type(number) not in (phonenumbers.PhoneNumberType.MOBILE,
                                                        phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE)):
        return None
    return "0" + str(number.national_number)  # +639171234567 -> 09171234567 (Semaphore's format)


def mask_mobile(number):
    """'09171234567' -> '0917 *** 4567' (shown in settings)."""
    return f"{number[:4]} *** {number[-4:]}" if number else None


def fit_message(text):
    """One segment: prefixed with NutriMatch, plain ASCII-friendly, ≤ 160 chars.
    Semaphore silently drops messages that start with "TEST", so the prefix
    also guards against that."""
    text = " ".join(str(text).split())
    text = text.replace("₱", "P").replace("—", "-").replace("–", "-").replace("’", "'")
    text = f"NutriMatch: {text}"
    return text if len(text) <= MAX_LENGTH else text[: MAX_LENGTH - 3].rstrip() + "..."


def send_sms(raw_number, text):
    """Send one SMS. Returns True when Semaphore accepted it."""
    number = normalize_ph_mobile(raw_number)
    if not number:
        return False
    message = fit_message(text)
    api_key = getattr(settings, "SEMAPHORE_API_KEY", "")
    if not api_key:
        logger.info("SMS not set up (SEMAPHORE_API_KEY blank) — would send to %s: %s", mask_mobile(number), message)
        return False
    data = {"apikey": api_key, "number": number, "message": message}
    sender = getattr(settings, "SEMAPHORE_SENDER_NAME", "")
    if sender:
        data["sendername"] = sender
    try:
        resp = httpx.post(SEMAPHORE_URL, data=data, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        first = body[0] if isinstance(body, list) and body else body
        status = (first or {}).get("status") if isinstance(first, dict) else None
        if status in ("Failed", "Refunded") or not isinstance(first, dict):
            logger.warning("Semaphore didn't send the SMS to %s: %s", mask_mobile(number), str(body)[:300])
            return False
        return True
    except httpx.HTTPStatusError as exc:
        # e.g. 403 while the Semaphore account is pending / has no credit:
        # keep the text in the log so it can still be shown what was sent.
        logger.warning("Semaphore refused the SMS (HTTP %s) to %s: %s", exc.response.status_code, mask_mobile(number), message)
        return False
    except Exception:
        logger.exception("Could not send SMS to %s: %s", mask_mobile(number), message)
        return False


def text_client(user, text):
    """A one-off SMS to a client who turned SMS on (Profile Settings ->
    Notifications): booking confirmed, consultation cancelled by the RND or
    NutriMatch. Sent after the database change is saved; returns whether
    it was queued (False when the client hasn't turned SMS on)."""
    from django.db import transaction

    from .models import ReminderPreference

    if getattr(user, "role", None) != "client" or not ReminderPreference.for_user(user).sms:
        return False
    phone = user.phone
    transaction.on_commit(lambda: send_sms(phone, text))
    return True
