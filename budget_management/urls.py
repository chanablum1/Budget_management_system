from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from transactions.serializers import CustomTokenObtainPairSerializer


urlpatterns = [
    path('admin/', admin.site.urls),
    path('income/', include('incomes.urls')),
    path('transaction/', include('transactions.urls')),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    

]
# 
# serializer_class=CustomTokenObtainPairSerializer