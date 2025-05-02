from rest_framework import filters, generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum

from accounts.models import User
from courses.models import Course
from orders.models import OrderItem, Order

from .serializers import AdminUserSerializer, AdminDashboardSerializer
from .utils import admin_revenue_stats


# Create your views here.
class AdminUserListView(generics.ListAPIView):
    """
    List all users with optional filtering by role (Only for Admins)
    """

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    queryset = User.objects.all().order_by("id")
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["id", "role", "email", "username"]

    def get_queryset(self):
        """
        Filter users by role if provided in the request
        """
        queryset = User.objects.all().order_by("id")
        role = self.request.query_params.get("role")
        print("role is ", role)
        if role:
            role_map = {"student": User.STUDENT, "instructor": User.INSTRUCTOR}
            if role.lower() in role_map:
                queryset = queryset.filter(role=role_map[role.lower()])
                print(queryset)

        return queryset


class AdminUserDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific user
    """

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    queryset = User.objects.all()
    lookup_field = "id"


class BlockUserView(generics.UpdateAPIView):
    """
    API to block a user (Admin only)
    """

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    queryset = User.objects.all()
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_blocked = True
        user.save()
        return Response(
            {"message": f"User {user.username} has been blocked"},
            status=status.HTTP_200_OK,
        )


class UnblockUserView(generics.UpdateAPIView):
    """
    API to Unblock a user (Admin Only)
    """

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    queryset = User.objects.all()
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_blocked = False
        user.save()
        return Response(
            {"message": f"User {user.username} has been unblocked"},
            status=status.HTTP_200_OK,
        )


class ActivateUserView(generics.UpdateAPIView):
    """
    API to Activate a User (Admin Only)
    """

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    queryset = User.objects.all()
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response(
            {"message": f"User {user.username} has been activated"},
            status=status.HTTP_200_OK,
        )


class AdminDashboardView(APIView):
    """
    API to List Dashboard details
    """

    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):

        # user stats in one query
        user_stats = User.objects.aggregate(
            total_students = Count(
                "id", filter=Q(role=User.STUDENT, is_active=True)
            ),
            active_students = Count(
                "id", filter=Q(role=User.STUDENT, is_blocked=False, is_active=True)
            ),
            total_instructors = Count(
                "id", filter=Q(role=User.INSTRUCTOR, is_active=True)
            ),
            active_instructors = Count(
                "id", filter=Q(role=User.INSTRUCTOR, is_active=True, is_blocked=False)
            )
        )


        # course stats in one query
        course_stats = Course.objects.aggregate(
            published_courses = Count(
                "id", filter=Q(status=Course.CourseStatus.PUBLISHED)
            ),
            pending_courses = Count(
                "id", filter=Q(status=Course.CourseStatus.PENDING)
            )
        )

        # order details 
        order_stats = OrderItem.objects.aggregate(
            total_enrollments = Count(
                "id", filter=Q(order__status=Order.OrderStatus.COMPLETED, is_refunded=False)
            ),
            cancelled_enrollments = Count(
                "id", filter=Q(is_refunded=True)
            ),
            total_revenue = Sum(
                "admin_earning", filter=Q(order__status=Order.OrderStatus.COMPLETED, is_refunded=False)
            )
        )

        # combine all stats
        dashboard_data = {**user_stats, **course_stats, **order_stats}

        serializer = AdminDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    
class AdminOrderRevenueStats(APIView):
    """
    API view to get the admin earning details
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        daily_revenue, monthly_revenue, last_12months, last_30days = (
            admin_revenue_stats()
        )

        return Response(
            {
                "status": "Success",
                "data": {
                    "daily_revenue": daily_revenue,
                    "monthly_revevnue": monthly_revenue,
                    "last_12months" : last_12months,
                    "last_30days": last_30days
                }
            },
            status=status.HTTP_200_OK
        )