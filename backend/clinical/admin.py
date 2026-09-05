from django.contrib import admin

from .models import NcpRecord, PreConsultationScreening, ProgressRecord

admin.site.register(PreConsultationScreening)
admin.site.register(NcpRecord)
admin.site.register(ProgressRecord)
