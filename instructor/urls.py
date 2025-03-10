from django.urls import path
from .views import InstructorResetPasswordView

urlpatterns = [
    path('reset-password/', InstructorResetPasswordView.as_view(), name="instructor-reset-password")
]
