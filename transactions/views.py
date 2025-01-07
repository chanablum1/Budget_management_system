from datetime import datetime, timedelta
import base64
import json
import urllib.parse

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

import pywhatkit as kit

from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer, UserSerializer
from users.models import SmartUser


@api_view(['POST'])
def login(request):
    # הכנס את הקוד המתאים כדי לזהות את המשתמש ולהחזיר את הטוקן
    username = request.data.get('username')
    password = request.data.get('password')

    # user = SmartUser.objects.get(username=username, password=password)  # כאן אתה שולף את המשתמש מתוך המודל SmartUser
    print(f"Received credentials: username={username}, password={password}")

    # user = authenticate(username=username, password=password)  # לדוגמה אם אתה משתמש ב-Django Auth

    try:
        user = SmartUser.objects.get(username=username, password=password)
        print(f"User {user.username} logged in successfully")  # <-- כאן ההדפסה


    # if user:
        # יצירת טוקן גישה ו-refresh
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # print(f"User {user.username} logged in successfully")  # הדפסת שם המשתמש בקונסול
        print(f"Username received: {username}")
        print(f"Password received: {password}")

            # שליחה של טוקנים ונתוני המשתמש
        return Response({
            'access': access_token,
            'refresh': refresh_token,
            'username': user.username , # החזרת שם המשתמש
                
        })

    except SmartUser.DoesNotExist:
        print("Invalid credentials")  # הדפסת שגיאה אם המשתמש לא נמצא

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# @api_view(['POST'])
# def register(request):
#     username = request.data.get('username')
#     password = request.data.get('password')
#     first_name = request.data.get('first_name')

#     # יצירת משתמש חדש
#     try:
#         user = SmartUser.objects.create_user(username=username, password=password, first_name=first_name)
        
#         # יצירת טוקן גישה ו-refresh
#         refresh = RefreshToken.for_user(user)
#         access_token = str(refresh.access_token)
#         refresh_token = str(refresh)

#         return Response({
#             'access': access_token,
#             'refresh': refresh_token,
#             'username': user.username
#         }, status=status.HTTP_201_CREATED)
    
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)    
@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    first_name = request.data.get('first_name', None)
    phone_number = request.data.get('phone_number', None)

    try:
        # יצירת משתמש חדש עם אימייל ומספר טלפון
        user = SmartUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
        )
        user.phone_number = phone_number
        user.save()

        # יצירת טוקנים
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            'access': access_token,
            'refresh': refresh_token,
            'username': user.username,
            'phone_number': user.phone_number,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Ensure user is authenticated
def get_user_info(request):
    user = request.user  # Get the authenticated user
    serializer = UserSerializer(user)
    return Response(serializer.data)


# ניהול קטגוריות
@api_view(['GET', 'POST'])
def category_list(request):
    if request.method == 'GET':
        category_type = request.query_params.get('type', None)
        if category_type == 'income':
            categories = Category.objects.filter(type='income')  
        elif category_type == 'expense':
            categories = Category.objects.filter(type='expense')      
        else:
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


@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, pk=None):
    # Retrieve a specific transaction
    if pk is not None:
        transaction = get_object_or_404(Transaction, pk=pk)
        if transaction.user != request.user:
            return Response(
                {"error": "You can only access your own transaction."},
                status=status.HTTP_403_FORBIDDEN,
            )
    
    # GET request handling
    if request.method == 'GET':
        if pk is None:
            # Filter transactions based on type query parameter
            transaction_type = request.query_params.get('type')
            if transaction_type == 'income':
                transactions = Transaction.objects.filter(user=request.user, category__type='income')
            elif transaction_type == 'expense':
                transactions = Transaction.objects.filter(user=request.user, category__type='expense')
            else:
                transactions = Transaction.objects.filter(user=request.user)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        else:
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data)

    # POST request handling
    elif request.method == 'POST':
        data = request.data
        try:
            category = Category.objects.get(id=data['category'])
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        if category.type not in ['income', 'expense']:
            return Response({'error': 'Invalid category type'}, status=status.HTTP_400_BAD_REQUEST)

        transaction = Transaction.objects.create(
            user=request.user,
            category=category,
            date=data['date'],
            amount=data['amount'],
            description=data['description'],
            payment_method=data.get('payment_method')
        )
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT request handling
    elif request.method == 'PUT':
        if pk is None:
            return Response({'error': 'Transaction ID required for updating'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        try:
            category = Category.objects.get(id=data.get('category', transaction.category.id))
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update transaction fields
        transaction.date = data.get('date', transaction.date)
        transaction.amount = data.get('amount', transaction.amount)
        transaction.category = category
        transaction.description = data.get('description', transaction.description)
        transaction.payment_method = data.get('payment_method', transaction.payment_method)
        
        transaction.save()
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)

    # DELETE request handling
    elif request.method == 'DELETE':
        if pk is None:
            return Response({'error': 'Transaction ID required for deletion'}, status=status.HTTP_400_BAD_REQUEST)

        transaction.delete()
        return Response({'message': 'Transaction deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

# סיכום חודשי
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # הוסף את הדקורטור הזה
def monthly_summary(request):
    user = request.user  # קבלת המשתמש המחובר

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
            total_income = Transaction.objects.filter(user=user, date__gte=start_date, date__lt=end_date, category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
            total_expense = Transaction.objects.filter(user=user, date__gte=start_date, date__lt=end_date, category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
            
            return Response({
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense,
                "month": f"{year}-{month:02d}"
            })
    except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# סיכום כללי טרם הוספתי אופציה זו
# @api_view(['GET'])
# # @permission_classes([IsAuthenticated])  # הוסף את הדקורטור הזה
# def summary_view(request):
#     user = request.user  # קבלת המשתמש המחובר

#     total_income = Transaction.objects.filter(category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
#     total_expense = Transaction.objects.filter(category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

#     return Response({
#         'total_income': total_income,
#         'total_expense': total_expense,
#         'balance': total_income - total_expense
#     })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_whatsapp_summary(request):
    user = request.user  # קבלת המשתמש המחובר

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
        total_income = Transaction.objects.filter(user=user, date__gte=start_date, date__lt=end_date, category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = Transaction.objects.filter(user=user, date__gte=start_date, date__lt=end_date, category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        
        balance = total_income - total_expense

        # אם היתרה נמוכה מ-10,000 ש"ח, נשלח הודעת וואטסאפ
        if balance < 10000:
            message = f"שלום {user.first_name}, הגעת למצב בו היתרה שלך בחודש {year}-{month} היא: {balance} ש\"ח, שהינה מתחת למגבלה של 10,000 ש\"ח."
            
            # שליחת הודעת WhatsApp מיידית
            kit.sendwhatmsg(f"+972{user.phone_number}", message, 12, 0, 15)
            
            # החזרת ערך של שליחה בהצלחה
            whatsapp_message_sent = True
        else:
            whatsapp_message_sent = False

        # מייבא את הסילייזר
        serializer = TransactionSerializer(data={
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "whatsapp_message_sent": whatsapp_message_sent,
            "month": f"{year}-{month:02d}"
        })

        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

