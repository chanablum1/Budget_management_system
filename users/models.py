from django.contrib.auth.models import AbstractUser
from django.db import models

class SmartUser(AbstractUser):
    # pass
    # favorite_color = models.CharField(max_length=30,null=True)  
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)  # שדה לאימייל
