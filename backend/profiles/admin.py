from django.contrib import admin

from .models import ClientHealthProfile, ClientProfile, RndAvailabilitySchedule, RndLanguage, RndProfile

admin.site.register(RndProfile)
admin.site.register(RndLanguage)
admin.site.register(RndAvailabilitySchedule)
admin.site.register(ClientProfile)
admin.site.register(ClientHealthProfile)
