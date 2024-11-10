from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list, name='category-list'),
    path('categories/<int:pk>/', views.category_detail, name='category-detail'),  # הוספת הפונקציה כאן
    path('transactions/', views.transaction_detail, name='transactions_list'),  # עדכון כאן אם אתה רוצה לפנות לפונקציה הזו
    path('transactions/<int:pk>/', views.transaction_detail, name='transactions_detail'),
    path('transactions/monthly-summary/', views.monthly_summary, name='transaction_monthly_summary'),  # עדכון לקריאה לפונקציה חודשית
    path('transactions/summary/', views.summary_view, name='transaction_summary'),  # עדכון לקריאה לפונקציה הסיכום
]



