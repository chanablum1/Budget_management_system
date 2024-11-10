from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer
from django.db.models import Sum
from users.models import SmartUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta

# ניהול קטגוריות
@api_view(['GET', 'POST'])
def category_list(request):
    if request.method == 'GET':
        category_type = request.query_params.get('type', None)
        if category_type == 'income':
            categories = Category.objects.filter(type='income')  # הצגת רק קטגוריות של הכנסה
        elif category_type == 'expense':
            categories = Category.objects.filter(type='expense')  # הצגת רק קטגוריות של הוצאה
        else:
            categories = Category.objects.all()  # ברירת מחדל - כל הקטגוריות

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

        # categories = Category.objects.all()
        # serializer = CategorySerializer(categories, many=True)
        # return Response(serializer.data)

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
@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def transaction_detail(request, pk=None):
    if request.method == 'GET':
        if pk is None:
            # סינון העסקאות לפי הטייפ (הכנסה או הוצאה)
            transaction_type = request.query_params.get('type', None)  # 'income' או 'expense'
            if transaction_type == 'income':
                transactions = Transaction.objects.filter(category__type='income')  # הצגת רק קטגוריות של הכנסה
            elif transaction_type == 'expense':
                transactions = Transaction.objects.filter(category__type='expense')  # הצגת רק קטגוריות של הוצאה
            else:
                transactions = Transaction.objects.all()  # ברירת מחדל - כל העסקאות

            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        # הצגת כל העיסקות אם pk לא הוזן
        # if pk is None:
        #     transactions = Transaction.objects.all()
        #     serializer = TransactionSerializer(transactions, many=True)
        #     return Response(serializer.data)
        else:
            try:
                transaction = Transaction.objects.get(pk=pk)
                serializer = TransactionSerializer(transaction)
                return Response(serializer.data)
            except Transaction.DoesNotExist:
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        # if not request.user.is_authenticated or request.user.id != 1:
        #     return Response({'error': 'Unauthorized user'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        try:
            category = Category.objects.get(id=data['category'])
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        if category.type not in ['income', 'expense']:
            return Response({'error': 'Invalid category type'}, status=status.HTTP_400_BAD_REQUEST)

        user = SmartUser.objects.get(id=1)
        # שימוש ביוזר קיים
        transaction = Transaction.objects.create(
            user=user,  # משתמש קיים (במקרה הזה עם ID 1)
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

                # קריאת נתוני הקטגוריה, במקרה הזה רק ה-ID מגיע
        category_id = request.data.get('category')  # מקבלים רק את ה-ID של הקטגוריה
        try:
            category = Category.objects.get(id=category_id)  # לא צריך את כל המילון, רק את ה-ID
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        # עדכון העיסקה עם הנתונים החדשים
        transaction.date = request.data.get('date', transaction.date)
        transaction.amount = request.data.get('amount', transaction.amount)
        transaction.category = category  # עדכון הקטגוריה לפי ה-ID
        transaction.description = request.data.get('description', transaction.description)
        transaction.payment_method = request.data.get('payment_method', transaction.payment_method)

        transaction.save()  # שמירת העדכון

        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)  # מחזירים את העיסקה המעודכנת
        # serializer = TransactionSerializer(transaction, data=request.data)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            transaction = Transaction.objects.get(pk=pk)
            transaction.delete()
            return Response({'message': 'Transaction deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

# סיכום חודשי
@api_view(['GET'])
def monthly_summary(request):
    # קבלת חודש ושנה מה-query params
    month = request.query_params.get('month', None)  # חודש בפורמט 'YYYY-MM'
    
    if not month:
        return Response({"error": "חודש לא צוין"}, status=status.HTTP_400_BAD_REQUEST)

    try:
            # המרת החודש (בשנה-חודש) לפורמט תאריך
            year, month = month.split("-")
            month = int(month)
            year = int(year)
            
            # סינון העסקאות לפי תאריך החודש והשנה
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
            
            # סיכום הכנסות והוצאות בחודש הנבחר
            total_income = Transaction.objects.filter(date__gte=start_date, date__lt=end_date, category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
            total_expense = Transaction.objects.filter(date__gte=start_date, date__lt=end_date, category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
            
            return Response({
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense,
                "month": f"{year}-{month:02d}"
            })
    except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# סיכום
@api_view(['GET'])
def summary_view(request):
    total_income = Transaction.objects.filter(category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

    # balance = total_income - total_expense


    return Response({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense
    })
