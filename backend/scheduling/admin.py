from django.contrib import admin

from .models import Appointment, ConsultationSession, Review, RndClientRelationship

admin.site.register(RndClientRelationship)
admin.site.register(Appointment)
admin.site.register(ConsultationSession)
admin.site.register(Review)
