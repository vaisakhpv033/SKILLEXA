from .views import CustomTokenObtainPairView, UserProfileView, RegisterUserView, AccountVerifyOTPView, GoogleLoginView
from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("google-login/", GoogleLoginView.as_view(), name="google-login"),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('register/verify/', AccountVerifyOTPView.as_view(), name='verify_otp'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
