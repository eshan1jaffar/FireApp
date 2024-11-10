from django.db import models

# Create your models here.
from django.db import models

# models.py

from django.db import models

class OverlayImage(models.Model):
    image = models.ImageField(upload_to='overlay_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Overlay Image created at {self.created_at}"
