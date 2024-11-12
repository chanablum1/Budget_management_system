from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer
from django.db.models import Sum
from users.models import SmartUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
import base64
import json



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

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    first_name = request.data.get('first_name')

    # יצירת משתמש חדש
    try:
        user = SmartUser.objects.create_user(username=username, password=password, first_name=first_name)
        
        # יצירת טוקן גישה ו-refresh
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            'access': access_token,
            'refresh': refresh_token,
            'username': user.username
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)    


# פונקציה לפענח את הטוקן ולקבל את שם המשתמש
def get_user_from_token(request):
    # שליפת הטוקן מה-header של הבקשה
    auth_header = request.headers.get('Authorization')
    if auth_header:
        # עיבוד ה-Bearer Token
        token = auth_header.split(" ")[1]  # מבודדים את הטוקן עצמו (לא את "Bearer")

        # פיצול הטוקן לחלקים (header, payload, signature)
        parts = token.split(".")
        if len(parts) == 3:
            # פענוח ה-Payload
            payload = base64.urlsafe_b64decode(parts[1] + "==")  # הוספת '==' כדי להפוך לפורמט חוקי של Base64
            decoded_payload = json.loads(payload)
            
            # שליפת המידע על המשתמש (כמו user_id או username)
            username = decoded_payload.get("username", None)
            return username
    return None

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    # קבלת שם המשתמש מתוך הטוקן
    username = get_user_from_token(request)

    if username:
        return Response({
            "username": username,
            "message": "User information retrieved successfully"
        })
    else:
        return Response({
            "error": "Invalid token or user information not found"
        }, status=400)

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


# פונקציה לניהול עסקאות
@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, pk=None):
    user = request.user  # קבלת המשתמש המחובר

    if request.method == 'GET':
        if pk is None:
            # סינון העסקאות לפי הטייפ (הכנסה או הוצאה)
            transaction_type = request.query_params.get('type', None)  
            if transaction_type == 'income':
                transactions = Transaction.objects.filter(category__type='income')  
            elif transaction_type == 'expense':
                transactions = Transaction.objects.filter(category__type='expense') 
            else:
                transactions = Transaction.objects.all()
                # filter(user=user)  

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

    elif request.method == 'DELETE':
        try:
            transaction = Transaction.objects.get(pk=pk)
            transaction.delete()
            return Response({'message': 'Transaction deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

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
@permission_classes([IsAuthenticated])  # הוסף את הדקורטור הזה
def summary_view(request):
    user = request.user  # קבלת המשתמש המחובר

    total_income = Transaction.objects.filter(category__type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Transaction.objects.filter(category__type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

    return Response({
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense
    })
