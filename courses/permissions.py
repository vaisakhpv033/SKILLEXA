from rest_framework.permissions import BasePermission

from accounts.models import User


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.ADMIN
        )


class IsAdminInstructor(BasePermission):
    """
    Allows admins and instructors access
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.role == User.ADMIN or request.user.role == User.INSTRUCTOR
            )
        )
