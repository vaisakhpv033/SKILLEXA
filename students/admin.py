from django.contrib import admin
from .models import Enrollments

# Register your models here.

class CustomEnrollmentAdmin(admin.ModelAdmin):
    """Custom admin for Enrollments model."""
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    list_display = (
        "student",
        "course",
        "enrolled_at",
    )
    ordering = ("-enrolled_at",)

admin.site.register(Enrollments, CustomEnrollmentAdmin)