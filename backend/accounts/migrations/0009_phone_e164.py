import phonenumbers
from django.db import migrations


def phones_to_e164(apps, schema_editor):
    """Phone numbers are now saved in E.164 (+639171234567) — see
    core.validators.validate_phone. Existing numbers were typed as local PH
    numbers (0917…), so they're read as Philippine. A number that can't be
    read is left as typed rather than deleted; the next profile save asks
    for a valid one."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.exclude(phone__isnull=True).exclude(phone=''):
        try:
            number = phonenumbers.parse(user.phone, 'PH')
        except phonenumbers.NumberParseException:
            continue
        if phonenumbers.is_valid_number(number):
            user.phone = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
            user.save(update_fields=['phone'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_user_welcome_seen_at'),
    ]

    operations = [
        migrations.RunPython(phones_to_e164, noop_reverse),
    ]
