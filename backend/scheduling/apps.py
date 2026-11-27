from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    name = 'scheduling'

    def ready(self):
        from django.db.models.signals import post_save

        from .models import Appointment
        from .reschedule import close_stale_proposals

        post_save.connect(close_stale_proposals, sender=Appointment, dispatch_uid="close_stale_proposals")
