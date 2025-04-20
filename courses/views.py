from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.models import User
from instructor.permissions import IsInstructor

from .models import Course, Topics
from .permissions import IsAdminInstructor, IsAdminUser
from .serializers import CourseSerializer, TopicsSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing courses.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        """Set permissions dynamically."""
        if self.action in ["create", "update", "destroy"]:
            return [IsInstructor()]
        elif self.action == "partial_update":
            return [IsAdminInstructor()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Ensure the instructor is set automatically."""
        serializer.save(instructor=self.request.user)

    def get_queryset(self):
        """Filter courses based on user role."""
        if self.request.user.is_authenticated:
            if getattr(self.request.user, "is_superuser", False):
                return Course.objects.filter(~Q(status=Course.CourseStatus.DRAFT))
            elif getattr(self.request.user, "role", False) == User.INSTRUCTOR:
                return Course.objects.filter(instructor=self.request.user)
        return Course.objects.filter(status=Course.CourseStatus.PUBLISHED)
    
    def perform_destroy(self, instance):
        if instance.instructor != self.request.user:
            raise PermissionDenied("You can only delete your own courses.")
        if instance.status != Course.CourseStatus.DRAFT:
            raise ValidationError("You can only delete draft courses.")
        super().perform_destroy(instance)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def published(self, request):
        """
        Endpoint to get published courses with optional filters:
        - ?level=1
        - ?category=3
        - ?subcategory=5
        """
        level = request.query_params.get("level")
        category = request.query_params.get("category")
        subcategory = request.query_params.get("subcategory")

        # Base queryset: only published courses
        queryset = Course.objects.filter(status=Course.CourseStatus.PUBLISHED)

        if level:
            queryset = queryset.filter(level=level)

        if subcategory:
            queryset = queryset.filter(topic_id=subcategory)
        elif category:
            # Find all subcategories and nested subcategories under this category
            subcategories = Topics.objects.filter(Q(parent_id=category) | Q(parent__parent_id=category)).values_list("id", flat=True)
            queryset = queryset.filter(topic_id__in=subcategories)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TopicsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing course categories and subcategories.
    - Admins can create and update categories.
    - Anyone can view categories and subcategories.
    """

    queryset = Topics.objects.all()
    serializer_class = TopicsSerializer

    def get_permissions(self):
        """Set permissions dynamically."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Return main categories if no parent is specified."""
        if self.action in ["retrieve", "update", "partial_update"]:
            print("returning all objects")
            return Topics.objects.all()
        parent_id = self.request.query_params.get("parent", None)
        print("none")
        if parent_id:
            print("returning parent_id")
            return Topics.objects.filter(parent_id=parent_id).order_by("id")
        return Topics.objects.filter(parent__isnull=True).order_by("id")

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single category along with its subcategories."""
        topic = get_object_or_404(Topics, pk=kwargs["pk"])
        serializer = self.get_serializer(topic)
        return Response(serializer.data)
