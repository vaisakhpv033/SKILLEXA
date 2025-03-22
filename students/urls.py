from django.urls import path
from .views import StudentResetPasswordView, StudentResetPasswordOTPView

urlpatterns = [
    path('reset-password/', StudentResetPasswordView.as_view(), name="student-reset-password"),
    path('reset-password/otp/', StudentResetPasswordOTPView.as_view(), name="student-reset-otp"),
]
