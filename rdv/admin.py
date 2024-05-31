from django.contrib import admin
from .models import *

admin.site.register(CUser)
admin.site.register(Like)
admin.site.register(Doctor)
admin.site.register(Admin)
admin.site.register(Patient)
admin.site.register(City)
admin.site.register(Specialty)
admin.site.register(Disponibility)
admin.site.register(Rdv)