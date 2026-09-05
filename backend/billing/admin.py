from django.contrib import admin

from .models import Invoice, PaymentTransaction

admin.site.register(Invoice)
admin.site.register(PaymentTransaction)
