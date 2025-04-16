from rest_framework import serializers
from .models import Sections, Lessons, Quizzes, Questions, AnswerOptions


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sections
        fields = ['id', 'title', 'course', 'order', 'created_at', 'updated_at']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lessons
        fields = ['id', 'title', 'content', 'video_url', 'video_duration', 'section', 'order']


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quizzes
        fields = ['id', 'title', 'lesson', 'order', 'min_pass_score']


class AnswerOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOptions
        fields = ['id', 'option_text', 'is_correct', 'question', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionsSerializer(many=True)
    class Meta:
        model = Questions
        fields = ['id', 'question_text', 'quiz', 'order', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options')
        question = Questions.objects.create(**validated_data)

        for option_data in options_data:
            AnswerOptions.objects.create(question=question, **option_data)

        return question
    
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if options_data is not None:
            # Clear existing options if provided
            instance.answer_options.all().delete()
            for option_data in options_data:
                AnswerOptions.objects.create(question=instance, **option_data)
        
        return instance




# Instructor curriculum serializers for reading nested data
class QuestionReadSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = Questions
        fields = ['id', 'question_text', 'quiz', 'order', 'answer_options']

class QuizReadSerializer(serializers.ModelSerializer):
    questions = QuestionReadSerializer(many=True, read_only=True)

    class Meta:
        model = Quizzes
        fields = ['id', 'title', 'lesson', 'order', 'min_pass_score', 'questions']

class LessonReadSerializer(serializers.ModelSerializer):
    quizzes = QuizReadSerializer(many=True, read_only=True)

    class Meta:
        model = Lessons
        fields = ['id', 'title', 'content', 'video_url', 'video_duration', 'section', 'order', 'quizzes']

class SectionDetailReadSerializer(serializers.ModelSerializer):
    lessons = LessonReadSerializer(many=True, read_only=True)

    class Meta:
        model = Sections
        fields = ['id', 'title', 'course', 'order', 'lessons', 'created_at', 'updated_at']




# Student curriculum serializers for reading nested data
class StudentQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quizzes
        fields = ["id", "title", "lesson", "order"]


class StudentLessonSerializer(serializers.ModelSerializer):
    quizzes = StudentQuizSerializer(many=True, read_only=True)

    class Meta:
        model = Lessons
        fields = ["id", "title", "order", "quizzes"]


class StudentSectionSerializer(serializers.ModelSerializer):
    lessons = StudentLessonSerializer(many=True, read_only=True)

    class Meta:
        model = Sections
        fields = ["id", "title", "course", "order", "lessons", "created_at", "updated_at"]
