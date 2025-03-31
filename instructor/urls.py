from django.urls import path

from .views import InstructorResetPasswordOTPView, InstructorResetPasswordView

urlpatterns = [
    path(
        "reset-password/",
        InstructorResetPasswordView.as_view(),
        name="instructor-reset-password",
    ),
    path(
        "reset-password/otp/",
        InstructorResetPasswordOTPView.as_view(),
        name="instructor-reset-otp",
    ),
]
