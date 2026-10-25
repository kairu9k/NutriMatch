"""RND payouts sent through Xendit (2026-10-26, user's call: the panel should
see a payout really go out, to GCash or a bank, in test mode).

PayMongo collects the clients' payments; its payout product needs a wallet
our account doesn't have, so payouts go through Xendit's Payouts API v2.
With a development key (xnd_development_...) nothing reaches the real
networks: Xendit simulates the transfer from a test balance, and a valid
payout ends SUCCEEDED. The admin still reviews and approves every run
(billing/payouts.py send_payout_via_xendit); Xendit's payout id becomes the
reference, so nobody types it. Manual recording stays as the fallback.

Settings: XENDIT_SECRET_KEY (Money-out write, Balance read) and
XENDIT_CALLBACK_TOKEN (Settings > Webhooks in Xendit's dashboard; the
callback header x-callback-token must match it).
"""

import time

import httpx
from django.conf import settings

BASE_URL = "https://api.xendit.co"
TIMEOUT = 20

# RndPayoutAccount.method -> Xendit channel code
WALLET_CHANNELS = {"gcash": "PH_GCASH", "maya": "PH_PAYMAYA", "gotyme": "PH_GOTYME", "maribank": "PH_SEA"}
# the bank names offered in Profile Settings (frontend utils/payout.js BANKS)
BANK_CHANNELS = {
    "bdo unibank": "PH_BDO", "bdo": "PH_BDO", "bpi": "PH_BPI", "metrobank": "PH_MET", "pnb": "PH_PNB",
    "security bank": "PH_SEC", "unionbank": "PH_UBP", "rcbc": "PH_RCBC", "china bank": "PH_CBC",
}

# Xendit's status -> ours
SUCCEEDED = {"SUCCEEDED"}
FAILED = {"FAILED", "CANCELLED", "REVERSED", "EXPIRED"}


class XenditError(Exception):
    pass


def secret_key():
    return (getattr(settings, "XENDIT_SECRET_KEY", "") or "").strip()


def configured():
    return bool(secret_key())


def is_test_mode():
    return secret_key().startswith("xnd_development_")


def _client():
    if not configured():
        raise XenditError("Xendit isn't set up (XENDIT_SECRET_KEY is empty).")
    return httpx.Client(base_url=BASE_URL, auth=(secret_key(), ""), timeout=TIMEOUT)


def _error(resp):
    try:
        body = resp.json()
        return body.get("message") or body.get("error_code") or resp.text[:200]
    except ValueError:
        return resp.text[:200]


_channels_cache = {"at": 0.0, "rows": []}


def channels():
    """Xendit's PHP payout channels, kept for a day in memory."""
    if _channels_cache["rows"] and time.time() - _channels_cache["at"] < 86400:
        return _channels_cache["rows"]
    with _client() as c:
        resp = c.get("/payouts_channels", params={"currency": "PHP"})
    if resp.status_code != 200:
        raise XenditError(f"Xendit didn't list its payout channels: {_error(resp)}")
    _channels_cache.update(at=time.time(), rows=resp.json())
    return _channels_cache["rows"]


def channel_for(account):
    """The Xendit channel code for an RND's payout details, or None when
    Xendit can't send there (then the admin records it manually)."""
    if account is None:
        return None
    if account.method in WALLET_CHANNELS:
        return WALLET_CHANNELS[account.method]
    name = (account.bank_name or "").strip().lower()
    if not name:
        return None
    if name in BANK_CHANNELS:
        return BANK_CHANNELS[name]
    try:
        for row in channels():
            if row.get("channel_category") == "BANK" and name in (row.get("channel_name") or "").lower():
                return row["channel_code"]
    except (XenditError, httpx.HTTPError):
        return None
    return None


def create_payout(*, idempotency_key, reference_id, channel_code, account_name, account_number, amount, description):
    """POST /v2/payouts. Returns Xendit's payout (id, status...)."""
    body = {
        "reference_id": reference_id,
        "channel_code": channel_code,
        "channel_properties": {"account_holder_name": account_name, "account_number": account_number},
        "amount": float(amount),
        "currency": "PHP",
        "description": description,
    }
    try:
        with _client() as c:
            resp = c.post("/v2/payouts", json=body, headers={"Idempotency-key": idempotency_key})
    except httpx.HTTPError as exc:
        raise XenditError(f"Couldn't reach Xendit: {exc.__class__.__name__}.") from exc
    if resp.status_code not in (200, 201):
        raise XenditError(f"Xendit refused the payout: {_error(resp)}")
    return resp.json()


def get_payout(payout_id):
    try:
        with _client() as c:
            resp = c.get(f"/v2/payouts/{payout_id}")
    except httpx.HTTPError as exc:
        raise XenditError(f"Couldn't reach Xendit: {exc.__class__.__name__}.") from exc
    if resp.status_code != 200:
        raise XenditError(f"Xendit didn't return the payout: {_error(resp)}")
    return resp.json()
