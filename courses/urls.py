from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, TopicsViewSet

router = DefaultRouter()
router.register(r"topics", TopicsViewSet)
router.register(r"courses", CourseViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
