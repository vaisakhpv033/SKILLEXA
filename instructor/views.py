from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import OtpVerification
from accounts.tasks import send_email
from accounts.throttles import OTPRequestThrottle

from .permissions import IsInstructor
from .serializers import InstructorResetPasswordSerializer

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.db.models import Count, Sum, Q
from decimal import Decimal

from courses.models import Course
from orders.models import OrderItem, Order


class InstructorResetPasswordOTPView(APIView):
    """API for Instructors to request OTP for password reset"""

    permission_classes = (IsAuthenticated, IsInstructor)
    throttle_classes = (OTPRequestThrottle,)

    def post(self, request):
        user = request.user

        # Generate OTP
        otp = OtpVerification.generate_otp(user, "password_reset")

        # Send OTP via email asynchronously using Celery
        subject = "Your OTP Code for Password Reset"
        message = f"Your OTP for password resetting is {otp}"
        send_email.delay(user.email, subject, message)

        return Response(
            {"message": "OTP sent to your email"}, status=status.HTTP_200_OK
        )


class InstructorResetPasswordView(generics.GenericAPIView):
    """Reset Password API view for authenticated Instructors"""

    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorResetPasswordSerializer

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



class InstructorDashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="overview")
    def overview(self, request):
        """
        Dashboard overview for authenticated instructors.
        """
        user = request.user

        if user.role != user.INSTRUCTOR:
            return Response({"detail": "Only instructors can access this endpoint."}, status=403)

        # Total courses created
        total_courses_created = Course.objects.filter(instructor=user).count()

        # Total published courses
        total_courses_published = Course.objects.filter(
            instructor=user,
            status=Course.CourseStatus.PUBLISHED
        ).count()

        # Total enrollments
        total_enrollments = OrderItem.objects.filter(
            instructor=user,
            is_refunded=False,
            order__status=Order.OrderStatus.COMPLETED
        ).count()

        # Total earnings (excluding refunded)
        total_earnings = OrderItem.objects.filter(
            instructor=user,
            is_refunded=False,
            order__status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum("instructor_earning"))["total"] or Decimal("0.00")

        # Locked earnings (in wallet)
        locked_earnings = user.wallet.locked_balance if hasattr(user, "wallet") else Decimal("0.00")

        # Top enrolled courses
        top_courses = (
            OrderItem.objects.filter(
                instructor=user,
                is_refunded=False,
                order__status=Order.OrderStatus.COMPLETED
            )
            .values("course__id", "course__title")
            .annotate(enrollments=Count("id"))
            .order_by("-enrollments")[:5]
        )

        return Response({
            "total_courses_created": total_courses_created,
            "total_courses_published": total_courses_published,
            "total_enrollments": total_enrollments,
            "total_earnings": total_earnings,
            "locked_earnings": locked_earnings,
            "top_enrolled_courses": list(top_courses)
        })