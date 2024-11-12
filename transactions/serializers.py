from rest_framework import serializers
from .models import Category, Transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import SmartUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # הוספת שם המשתמש ל-token
        token['username'] = user.username
        token['first_name'] = user.first_name  # הוספת השם הפרטי
        # ניתן להוסיף כאן עוד מידע שתרצה להחזיר בתוך ה-token
        
        return token

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

        
class TransactionSerializer(serializers.ModelSerializer):
    # category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # רק ה-ID של הקטגוריה

    category = CategorySerializer() 
    # user = CustomTokenObtainPairSerializer()
    # username = serializers.CharField(source='user.username', read_only=True)

    
    class Meta:
        model = Transaction
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SmartUser
        fields = [ "username"]







