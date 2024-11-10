from rest_framework import serializers
from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

        
class TransactionSerializer(serializers.ModelSerializer):
    # category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # רק ה-ID של הקטגוריה

    category = CategorySerializer() 

    class Meta:
        model = Transaction
        fields = '__all__'






