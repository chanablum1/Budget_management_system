from django.urls import path
from . import views

urlpatterns = [
    path('incomes/', views.income_list, name='income_list'),
    path('incomes/<int:pk>/', views.income_detail, name='income_detail'),
]
