from django.db import models

# Create your models here.

class Marker(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    urgency = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])

    def __str__(self):
        return f"Marker at ({self.latitude}, {self.longitude}) - {self.urgency}"