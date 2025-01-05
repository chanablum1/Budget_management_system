from rest_framework import serializers
from .models import SmartUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartUser
        fields = ['id', 'username', 'phone_number']
