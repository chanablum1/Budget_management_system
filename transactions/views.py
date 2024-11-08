from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer
import json
from django.db.models import Sum
from users.models import SmartUser

# ניהול קטגוריות
@api_view(['GET', 'POST'])
def category_list(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET', 'PUT', 'DELETE'])
def category_detail(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        category.delete()
        return Response({'message': 'Category deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# פונקציה לניהול עסקאות
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def transaction_detail(request, pk=None):
    if request.method == 'GET':
        # הצגת כל העיסקות אם pk לא הוזן
        if pk is None:
            transactions = Transaction.objects.all()
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        else:
            try:
                transaction = Transaction.objects.get(pk=pk)
                serializer = TransactionSerializer(transaction)
                return Response(serializer.data)
            except Transaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        if not request.user.is_authenticated or request.user.id != 1:
            return Response({'error': 'Unauthorized user'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        try:
            category = Category.objects.get(id=data['category'])
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        if category.type not in ['income', 'expense']:
            return Response({'error': 'Invalid category type'}, status=status.HTTP_400_BAD_REQUEST)

        # שימוש ביוזר קיים
        transaction = Transaction.objects.create(
            user=request.user,  # משתמש קיים (במקרה הזה עם ID 1)
            category=category,
            date=data['date'],
            amount=data['amount'],
            description=data['description'],
            payment_method=data.get('payment_method')  # אם יש אמצעי תשלום
        )
        
        return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)

    elif request.method == 'PUT':
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TransactionSerializer(transaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            transaction = Transaction.objects.get(pk=pk)
            transaction.delete()
            return Response({'message': 'Transaction deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

# סיכום
@api_view(['GET'])
def summary_view(request):
    total_income = Transaction.objects.filter(category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

    return Response({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense
    })
