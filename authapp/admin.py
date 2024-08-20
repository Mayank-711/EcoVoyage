from django.contrib import admin
from .models import *
# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','location', 'contact')  # Fields to display in the list view
    search_fields = ('user_username', 'location', 'contact')     # Fields to include in search
admin.site.register(UserProfile, UserProfileAdmin) 