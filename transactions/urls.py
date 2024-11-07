from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list, name='category-list'),
    path('categories/<int:pk>/', views.category_detail, name='category-detail'),  # הוספת הפונקציה כאן
    path('transactions/', views.transaction_detail, name='transactions_list'),  # עדכון כאן אם אתה רוצה לפנות לפונקציה הזו
    path('transactions/<int:pk>/', views.transaction_detail, name='transactions_detail'),
    # path('transactions/income/', views.add_income, name='add_income'),  # ודא שהפונקציה הזו קיימת ב-views
    path('transactions/summary/', views.summary_view, name='transaction_summary'),  # עדכון לקריאה לפונקציה הסיכום
]



# urlpatterns = [
#     path('categories/', views.category_list, name='category-list'),
#     path('categories/<int:pk>/', views.category_detail, name='category-detail'),
#     path('transactions/', views.transaction_list, name='transactions_list'),
#     path('transactions/<int:pk>/', views.transaction_detail, name='transactions_detail'),
#     path('transactions/income/', views.add_income, name='add_income'), 
#     path('transactions/expense/', views.transaction_list, name='expense_list'),
#     path('transactions/summary/', views.transaction_list, name='transaction_summary'),
# ]
