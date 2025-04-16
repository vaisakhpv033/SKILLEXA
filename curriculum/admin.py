from django.contrib import admin
from .models import Sections, Lessons, Questions, Quizzes, AnswerOptions

# Register your models here.
admin.site.register(Sections)
admin.site.register(Lessons)
admin.site.register(Questions)
admin.site.register(Quizzes)
admin.site.register(AnswerOptions)