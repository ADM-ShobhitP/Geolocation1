from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    Role_Choices = (
        ('Data Collector', "DC"),
        ('Approver', "AP"),
        ('SuperAdmin', "SA"),    
    )
    role = models.CharField(max_length=20, choices=Role_Choices)

    def __str__(self):
        return self.username

class Plant(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
class PlantBoundary(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name="boundaries")
    latitude  = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"Boundary for {self.plant.name} at ({self.latitude}, {self.longitude})"


class Schedule(models.Model):
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="approver_scheduled", limit_choices_to={'role': 'Approver'})
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    collectors = models.ManyToManyField(User, related_name="data_collector_scheduled", limit_choices_to={'role': 'Data Collector'})
    visit_date =  models.DateField()

    def __str__(self):
        print(self.collectors)
        return f"Schedule on {self.plant.name} at {self.visit_date} by {self.approver}"
    
class DataCollector(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, default=13)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    Name_client = models.CharField(max_length=200)
    Designation_client = models.CharField(max_length=200)
    Email_client = models.CharField(max_length=200)
    Contact_client = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    visit_date = models.DateField()
    dc_location_lat = models.FloatField(default=0.0)
    dc_location_long = models.FloatField(default=0.0)