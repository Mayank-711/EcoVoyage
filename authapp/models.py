from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forgot_password_token = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=30, blank=True, null=True)
    contact = models.IntegerField(blank=True,null=True)
    avatar = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='friends_from', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friends_to', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)  # Track if the request has been accepted

    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = 'Friendship'
        verbose_name_plural = 'Friendships'

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({'Accepted' if self.accepted else 'Pending'})"

    @staticmethod
    def friends(user):
        friends = set()
        friendships = Friendship.objects.filter(from_user=user, accepted=True) | Friendship.objects.filter(to_user=user, accepted=True)
        for friendship in friendships:
            if friendship.from_user == user:
                friends.add(friendship.to_user)
            else:
                friends.add(friendship.from_user)
        return friends