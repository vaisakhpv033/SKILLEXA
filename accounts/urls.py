from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView

from .views import (
    AccountVerifyOTPView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    ForgotPasswordOTPView,
    ForgotPasswordResetView,
    GoogleLoginView,
    RegisterUserView,
    ResendOTPView,
    UserProfileView,
    FirebaseTokenAddView
)

urlpatterns = [
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", TokenBlacklistView.as_view(), name="'token_blacklist"),
    path("google-login/", GoogleLoginView.as_view(), name="google-login"),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("register/verify/", AccountVerifyOTPView.as_view(), name="verify_otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("forgot-password/otp/", ForgotPasswordOTPView.as_view(), name="forgot-otp"),
    path("forgot-password/", ForgotPasswordResetView.as_view(), name="forgot-password"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path('fcm-token/', FirebaseTokenAddView.as_view(), name='fcm-token')
]
