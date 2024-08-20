from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forgot_password_token = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=30, blank=True)
    contact = models.IntegerField(blank=True,null=True)
    avatar = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.user.username