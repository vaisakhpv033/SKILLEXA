from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, TopicsViewSet, CommentViewSet

router = DefaultRouter()
router.register(r"topics", TopicsViewSet)
router.register(r"courses", CourseViewSet)
router.register(r"comments", CommentViewSet, basename="comments")

urlpatterns = [
    path("", include(router.urls)),
]

