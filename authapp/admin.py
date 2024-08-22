from django.contrib import admin
from .models import *
# Register your models here.
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','pincode', 'contact')  # Fields to display in the list view
    search_fields = ('user_username', 'pincode', 'contact')     # Fields to include in search
admin.site.register(UserProfile, UserProfileAdmin) 

class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at', 'accepted')  # Fields to display in the list view
    search_fields = ('from_user__username', 'to_user__username')        # Fields to include in search
    list_filter = ('accepted',)                                         # Fields to filter by
    
admin.site.register(Friendship, FriendshipAdmin)  # Register the model with the custom admin class