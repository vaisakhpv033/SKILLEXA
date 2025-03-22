from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.throttles import OTPRequestThrottle
from accounts.tasks import send_email
from accounts.models import OtpVerification

from .permissions import IsStudent
from .serializers import StudentResetPasswordSerializer



class StudentResetPasswordOTPView(APIView):
    """  API for Instructors to request OTP for password reset """
    permission_classes = (IsAuthenticated, IsStudent)
    throttle_classes = (OTPRequestThrottle,)

    def post(self, request):
        user = request.user 

        # Generate OTP
        otp = OtpVerification.generate_otp(user, "password_reset")

        # Send OTP via email asynchronously using Celery
        subject = "Your OTP Code for Password Reset"
        message = f"Your OTP for password resetting is {otp}"
        send_email.delay(user.email, subject, message)

        return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)

class StudentResetPasswordView(generics.GenericAPIView):
    """Reset Password API view for authenticated Instructors"""

    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = StudentResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password Reset Successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


