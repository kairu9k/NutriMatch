from .models import NotificationLog


def notify(recipient, notifiable_type, notifiable_id, subject, content):
    """Creates an in-app notification. IN_APP notifications are considered
    delivered immediately — there's no external delivery step to track."""
    return NotificationLog.objects.create(
        recipient=recipient,
        notifiable_type=notifiable_type,
        notifiable_id=notifiable_id,
        channel=NotificationLog.Channel.IN_APP,
        subject=subject,
        content=content,
        status=NotificationLog.Status.DELIVERED,
    )
