from django.urls import path

from .views import StudentResetPasswordOTPView, StudentResetPasswordView, EnrolledCoursesView

urlpatterns = [
    path(
        "reset-password/",
        StudentResetPasswordView.as_view(),
        name="student-reset-password",
    ),
    path(
        "reset-password/otp/",
        StudentResetPasswordOTPView.as_view(),
        name="student-reset-otp",
    ),
    path(
        "enrolled-courses/",
        EnrolledCoursesView.as_view(),
        name="student-enrolled-courses",
    ),
]
