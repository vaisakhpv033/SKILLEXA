from .views import CustomTokenObtainPairView
from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
