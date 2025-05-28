from django.contrib import admin
from .models import CustomUser, Team

admin.site.register(Team)
admin.site.register(CustomUser)
