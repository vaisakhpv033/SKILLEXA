from rest_framework.permissions import BasePermission, SAFE_METHODS

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


class IsEnrolledOrInstructorOrAuthor(BasePermission):
    """
    Allows access only to:
    - Enrolled students
    - Course instructor
    - Comment author for unsafe methods
    """

    def has_object_permission(self, request, view, obj):
        user = request.user 
        if request.method in SAFE_METHODS:
            return obj.course.instructor == user or obj.course.enrollments.filter(student=user).exists()
        
        if request.method in ["PATCH", "PUT", "DELETE"]:
            return obj.user == user 
        
        return False 
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            course_id = request.query_params.get("course")
            if not course_id:
                return False 
            
            from courses.models import Course 
            from students.models import Enrollments

            try:
                course = Course.objects.get(id=course_id)
                return course.instructor == request.user or Enrollments.objects.filter(student=request.user, course=course).exists()
            except Course.DoesNotExist:
                return False
        return True