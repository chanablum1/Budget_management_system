from django.db import models
from users.models import SmartUser

class Income(models.Model):
    user = models.ForeignKey(SmartUser, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=100)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

