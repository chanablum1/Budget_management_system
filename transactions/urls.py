from django.urls import path
from . import views

urlpatterns = [
    path('user/', views.get_user_info, name='get_user_info'),  
    path('register/', views.register, name="register"),
    path('categories/', views.category_list, name='category-list'),
    path('categories/<int:pk>/', views.category_detail, name='category-detail'),
    path('transactions/', views.transaction_detail, name='transactions_list'), 
    path('transactions/<int:pk>/', views.transaction_detail, name='transactions_detail'),
    path('transactions/monthly-summary/', views.monthly_summary, name='transaction_monthly_summary'),  
    path('transactions/monthly_summary_email/', views.monthly_summary_email, name='monthly_summary_email'),

    # path('transactions/summary/', views.summary_view, name='transaction_summary'),  
]





