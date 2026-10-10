from django.contrib import admin

from .models import Message, NotificationLog, Reminder, Resource, ResourceShare

admin.site.register(Message)
admin.site.register(Resource)
admin.site.register(ResourceShare)
admin.site.register(Reminder)
admin.site.register(NotificationLog)
