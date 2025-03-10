from .views import CustomTokenObtainPairView, UserProfileView, RegisterUserView, AccountVerifyOTPView, GoogleLoginView, ResendOTPView, ForgotPasswordOTPView, ForgotPasswordResetView, CustomTokenRefreshView
from django.urls import path

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),

    path("google-login/", GoogleLoginView.as_view(), name="google-login"),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('register/verify/', AccountVerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name="resend-otp"),
    path('forgot-password/otp/', ForgotPasswordOTPView.as_view(), name="forgot-otp"),
    path('forgot-password/', ForgotPasswordResetView.as_view(), name="forgot-password"),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
