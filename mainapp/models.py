from django.db import models
from django.contrib.auth.models import User

class TravelLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source_address = models.CharField(max_length=255)
    destination_address = models.CharField(max_length=255)
    source_latitude = models.FloatField()
    source_longitude = models.FloatField()
    destination_latitude = models.FloatField()
    destination_longitude = models.FloatField()
    distance = models.FloatField()
    date = models.DateField()
    time_taken = models.CharField(max_length=100)
    time_duration_fetched = models.CharField(max_length=100)  # New field
    is_electric = models.BooleanField()
    mode_of_transport = models.CharField(max_length=50)
    carbon_footprint = models.FloatField()
    log_time = models.TimeField()
    def __str__(self):
        return f"{self.user.username} - {self.source_address} to {self.destination_address}"

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user
    source_lat = models.FloatField()
    source_lng = models.FloatField()
    dest_lat = models.FloatField()
    dest_lng = models.FloatField()
    source_address = models.CharField(max_length=255)
    destination_address = models.CharField(max_length=255)
    search_date = models.DateField()
    search_time = models.TimeField()
    distance = models.FloatField()
    duration = models.FloatField()
    carbon_footprint = models.JSONField()  # Store carbon footprint data in JSON format

    def __str__(self):
        return f"Trip from {self.source_address} to {self.destination_address} on {self.search_date}"