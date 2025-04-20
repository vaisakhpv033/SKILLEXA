from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Sections, Lessons, Quizzes, Questions
from .serializers import (
        SectionSerializer,
        LessonSerializer,
        QuizSerializer,
        QuestionSerializer,
        StudentSectionSerializer,
        SectionDetailReadSerializer,
    )
from rest_framework.permissions import AllowAny
from .mixins import InstructorOwnedContentMixin
from students.models import Enrollments
from students.permissions import IsStudent



class SectionViewSet(InstructorOwnedContentMixin, ModelViewSet):
    """
    ViewSet for managing sections.
    Only instructors can create, edit, and delete sections.
    """
    queryset = Sections.objects.all()
    serializer_class = SectionSerializer

    def get_queryset(self):
        base_qs =  super().get_queryset() # calls the mixin's get_queryset method

        course_id = self.request.query_params.get('course_id')
        if course_id:
            return base_qs.filter(course_id=course_id)
        return base_qs
    
    @action(detail=False, methods=['get'], url_path='by-course/(?P<course_id>[^/.]+)')
    def list_by_course(self, request, course_id=None):
        """
        Custom route to list all sections of a particular course.
        """
        sections = self.queryset.filter(course_id=course_id, course__instructor=request.user).prefetch_related('lessons__quizzes__questions__answer_options')
        serializer = SectionDetailReadSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='enrolled-course/(?P<course_id>[^/.]+)', permission_classes=[IsStudent])
    def list_enrolled_course(self, request, course_id=None):
        """
        Custom route to list the curriculum details of a student's enrolled course
        """
        try:
            user = request.user
            Enrollments.objects.get(student=user, course__id=course_id)
        except Enrollments.DoesNotExist:
            return Response({"detail": "Enrollment not found."}, status=404)
        sections = self.queryset.filter(course_id=course_id).prefetch_related('lessons__quizzes__questions__answer_options')
        serializer = SectionDetailReadSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='student/(?P<course_id>[^/.]+)', permission_classes=[AllowAny])
    def list_student_curriculum(self, request, course_id=None):
        """
        Custom route to list course curriculum structure
        """

        sections = self.queryset.filter(course_id=course_id).prefetch_related('lessons__quizzes')
        serializer = StudentSectionSerializer(sections, many=True)

        return Response(serializer.data)



class LessonViewSet(InstructorOwnedContentMixin, ModelViewSet):
    """
    ViewSet for managing lessons.
    Only instructors can create, edit, and delete lessons.
    """
    queryset = Lessons.objects.all()
    serializer_class = LessonSerializer


class QuizViewSet(InstructorOwnedContentMixin, ModelViewSet):
    """
    ViewSet for managing quizzes.
    """
    queryset = Quizzes.objects.all()
    serializer_class = QuizSerializer


class QuestionAnswerViewSet(InstructorOwnedContentMixin, ModelViewSet):
    """
    ViewSet for managing questions and answers of a quizz. 
    """

    queryset = Questions.objects.all()
    serializer_class = QuestionSerializer




    # @action(detail=False, methods=['post'], url_path='bulk-create')
    # def bulk_create(self, request):
    #     """
    #     Custom endpoint to create multiple lessons, quizzes, questions, and answers at once.
    #     """
    #     lessons_data = request.data.get('lessons', [])
    #     if not lessons_data:
    #         return Response({"error": "Lessons data is required."}, status=status.HTTP_400_BAD_REQUEST)

    #     created_lessons = []

    #     with transaction.atomic():
    #         for lesson_data in lessons_data:
    #             quizzes_data = lesson_data.pop('quizzes', [])
    #             lesson_serializer = LessonSerializer(data=lesson_data)
    #             if lesson_serializer.is_valid():
    #                 lesson = lesson_serializer.save()
    #                 created_lessons.append({
    #                     "lesson": lesson_serializer.data,
    #                     "quizzes": []
    #                 })

    #                 # Create quizzes for the lesson if provided
    #                 for quiz_data in quizzes_data:
    #                     questions_data = quiz_data.pop('questions', [])
    #                     quiz_data['lesson'] = lesson.id
    #                     quiz_serializer = QuizSerializer(data=quiz_data)
    #                     if quiz_serializer.is_valid():
    #                         quiz = quiz_serializer.save()
    #                         created_lessons[-1]["quizzes"].append({
    #                             "quiz": quiz_serializer.data,
    #                             "questions": []
    #                         })

    #                         # Create questions for the quiz if provided
    #                         for question_data in questions_data:
    #                             answer_options_data = question_data.pop('answers', [])
    #                             question_data['quiz'] = quiz.id
    #                             question_serializer = QuestionSerializer(data=question_data)
    #                             if question_serializer.is_valid():
    #                                 question = question_serializer.save()
    #                                 created_lessons[-1]["quizzes"][-1]["questions"].append({
    #                                     "question": question_serializer.data,
    #                                     "answers": []
    #                                 })

    #                                 # Create answer options for the question if provided
    #                                 for answer_option_data in answer_options_data:
    #                                     answer_option_data['question'] = question.id
    #                                     answer_option_serializer = AnswerOptionsSerializer(data=answer_option_data)
    #                                     if answer_option_serializer.is_valid():
    #                                         answer_option_serializer.save()
    #                                         created_lessons[-1]["quizzes"][-1]["questions"][-1]["answers"].append(
    #                                             answer_option_serializer.data
    #                                         )
    #                                     else:
    #                                         return Response({
    #                                             "error": "Invalid answer data",
    #                                             "details": answer_option_serializer.errors,
    #                                         }, status=status.HTTP_400_BAD_REQUEST)
    #                             else:
    #                                 return Response({
    #                                     "error": "Invalid question data",
    #                                     "details": question_serializer.errors,
    #                                 }, status=status.HTTP_400_BAD_REQUEST)
    #                     else:
    #                         return Response({
    #                             "error": "Invalid quiz data",
    #                             "details": quiz_serializer.errors,
    #                         }, status=status.HTTP_400_BAD_REQUEST)
    #             else:
    #                 return Response({
    #                     "error": "Invalid lesson data",
    #                     "details": lesson_serializer.errors,
    #                 }, status=status.HTTP_400_BAD_REQUEST)

    #     return Response({
    #         "message": "Lessons created successfully",
    #         "lessons": created_lessons
    #     }, status=status.HTTP_201_CREATED)

