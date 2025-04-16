from django.db import models

# Create your models here.
class Sections(models.Model):
    """
    Represents sections within a course.

    Each section can contain multiple lessons.
    """

    title = models.CharField(max_length=100)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="sections"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Sections"

    def __str__(self):
        return self.title
    
    @classmethod
    def filter_by_instructor(cls, instructor):
        """
        Filter sections by instructor.
        """
        return cls.objects.filter(course__instructor=instructor)
    
    def get_course(self):
        """
        Get the course associated with this section.
        """
        return self.course
    

class Lessons(models.Model):
    """
    Represents lessons within a section of a course.

    Each lesson can contain multiple quizzes.
    """

    title = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    video_duration = models.PositiveIntegerField(blank=True, null=True)
    section = models.ForeignKey(
        "Sections", on_delete=models.CASCADE, related_name="lessons"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Lessons"

    def __str__(self):
        return self.title
    
    @classmethod
    def filter_by_instructor(cls, instructor):
        """
        Filter lessons by instructor.
        """
        return cls.objects.filter(section__course__instructor=instructor)
    
    def get_course(self):
        """
        Get the course associated with this lesson.
        """
        return self.section.course
    

class Quizzes(models.Model):
    """
    Represents quizzes within a lesson.

    Each quiz can have multiple questions.
    """

    title = models.CharField(max_length=100)
    lesson = models.ForeignKey(
        "Lessons", on_delete=models.CASCADE, related_name="quizzes"
    )
    order = models.PositiveIntegerField(default=0)
    min_pass_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title
    
    @classmethod 
    def filter_by_instructor(cls, instructor):
        """
        Filter quizzes by instructor.
        """
        return cls.objects.filter(lesson__section__course__instructor=instructor)
    
    def get_course(self):
        """
        Get the course associated with this quiz.
        """
        return self.lesson.section.course
    

class Questions(models.Model):
    """
    Represents questions within a quiz.

    Each question can have multiple answer options.
    """

    question_text = models.TextField()
    quiz = models.ForeignKey(
        "Quizzes", on_delete=models.CASCADE, related_name="questions"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Questions"

    def __str__(self):
        return self.question_text
    
    @classmethod
    def filter_by_instructor(cls, instructor):
        """
        Filter questions by instructor.
        """
        return cls.objects.filter(quiz__lesson__section__course__instructor=instructor)
    
    def get_course(self):
        """
        Get the course associated with this question.
        """
        return self.quiz.lesson.section.course
    

class AnswerOptions(models.Model):
    """
    Represents answer options for a question.

    Each question can have multiple answer options.
    """

    option_text = models.TextField()
    question = models.ForeignKey(
        "Questions", on_delete=models.CASCADE, related_name="answer_options"
    )
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Answer Options"

    def __str__(self):
        return self.option_text
    

class StudentQuizAttempts(models.Model):
    """
    Represents a student's attempt at a quiz.

    Each attempt can have multiple answers submitted by the student.
    """

    student = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(
        "Quizzes", on_delete=models.CASCADE, related_name="student_attempts"
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    is_passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Student Quiz Attempts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"
    

class StudentLessonProgress(models.Model):
    """
    Represents a student's progress in a lesson.
    """
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey("Lessons", on_delete=models.CASCADE, related_name="student_progress")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        verbose_name_plural = "Student Lesson Progress"
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"