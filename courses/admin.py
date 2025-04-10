from django.contrib import admin

from .models import Course, CourseDetail, PriceLevel, Topics


# Custom Topics Admin
@admin.register(Topics)
class TopicsAdmin(admin.ModelAdmin):
    """
    Custom admin for Topics model.
    Displays categories and subcategories.
    """

    @admin.display(description="Category Type")
    def category_type_display(self, obj):
        return "Category" if obj.parent is None else "Subcategory"

    @admin.display(description="Total Courses")
    def total_course(self, obj):
        return obj.courses.count()  # related_name='courses' in Course model

    list_display = (
        "name",
        "category_type_display",
        "parent",
        "total_course",
        "score",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = ("parent", "created_at")
    readonly_fields = ("score", "created_at", "updated_at")


# Custom Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Custom admin for Course model.
    Displays course information with instructor and topic details.
    """

    list_display = (
        "title",
        "instructor",
        "topic",
        "price",
        "level",
        "status",
        "created_at",
    )
    search_fields = (
        "title",
        "instructor__username",
        "instructor__email",
        "topic__name",
    )
    list_filter = ("status", "level", "language", "created_at")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ["topic", "instructor"]


# Custom Course Detail Admin
@admin.register(CourseDetail)
class CourseDetailAdmin(admin.ModelAdmin):
    """
    Custom admin for CourseDetail model.
    Displays additional course information like requirements, outcomes, and target audience.
    """

    @admin.display(description="Short Description")
    def short_description(self, obj):
        return (
            obj.description[:75] + "..."
            if len(obj.description) > 75
            else obj.description
        )

    list_display = ("course", "detail_type", "short_description", "created_at")
    search_fields = ("course__title", "detail_type")
    list_filter = ("detail_type", "created_at")
    readonly_fields = ("created_at", "updated_at")


# Custom Price Level Admin
@admin.register(PriceLevel)
class PriceLevelAdmin(admin.ModelAdmin):
    """
    Custom admin for PriceLevel model.
    Displays and manages price levels with a soft-delete mechanism.
    """

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        return obj.deleted_at is None

    @admin.action(description="Restore selected Price Levels")
    def restore_price_levels(self, request, queryset):
        queryset.update(deleted_at=None)

    list_display = ("name", "amount", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("deleted_at",)
    readonly_fields = ("created_at", "updated_at")
    actions = [restore_price_levels]
