from django.db import models

# Create your models here.
class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    feedback = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

from django.db import models

class Store(models.Model):
    store_id = models.AutoField(primary_key=True)  # Auto-incrementing ID field
    store_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)

    def __str__(self):
        return self.store_name
