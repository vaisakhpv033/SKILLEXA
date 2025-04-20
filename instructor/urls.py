from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstructorResetPasswordOTPView, InstructorResetPasswordView, InstructorDashboardViewSet

router = DefaultRouter()
router.register(r"instructor-dashboard", InstructorDashboardViewSet, basename="instructor-dashboard")

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
    path('', include(router.urls))
]
