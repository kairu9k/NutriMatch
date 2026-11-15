"""Saving an RND's GCash/bank payout details, shared by the Earnings page
(PUT /api/rnd/payout-account/) and the RND onboarding."""
from django.utils import timezone

from core.models import AuditLog

from .models import RndPayoutAccount
from .serializers import RndPayoutAccountSerializer


def save_payout_account(rnd, data):
    """Validates `data` and creates or replaces the RND's payout account.
    Raises a DRF ValidationError. Stamps details_changed_at on a real change
    (the admin sees a warning for a week after, before releasing a payout)."""
    account = RndPayoutAccount.objects.filter(rnd=rnd).first()
    before = (account.method, account.account_name, account.account_number, account.bank_name) if account else None
    serializer = RndPayoutAccountSerializer(account, data=data)
    serializer.is_valid(raise_exception=True)
    saved = serializer.save(rnd=rnd)
    changed = before != (saved.method, saved.account_name, saved.account_number, saved.bank_name)
    if changed:
        saved.details_changed_at = timezone.now()
        saved.save(update_fields=["details_changed_at"])
    AuditLog.objects.create(
        user=rnd, action="payout_account.updated", table_name="rnd_payout_accounts",
        record_id=saved.id, new_values={"method": saved.method, "details_changed": changed},
    )
    return saved
