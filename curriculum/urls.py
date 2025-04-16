from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SectionViewSet, LessonViewSet, QuizViewSet, QuestionAnswerViewSet

router = DefaultRouter()
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'quizz', QuizViewSet, basename='quiz')
router.register(r'questions', QuestionAnswerViewSet, basename='question')

urlpatterns = [
    path('', include(router.urls)),
]