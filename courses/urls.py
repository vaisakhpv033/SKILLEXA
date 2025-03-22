from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TopicsViewSet, CourseViewSet

router = DefaultRouter()
router.register(r"topics", TopicsViewSet)
router.register(r"courses", CourseViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
