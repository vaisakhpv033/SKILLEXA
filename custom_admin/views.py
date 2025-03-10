from rest_framework import filters, generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import User

from .serializers import AdminUserSerializer


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
