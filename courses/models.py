from django.db import models
from django.utils import timezone


class Topics(models.Model):
    """
    Represents course categories and subcategories.

    Hierarchy:
    - If `parent` is NULL → it's a **main category**.
    - If `parent` has a value → it's a **subcategory**.
    - A subcategory can have its own subcategories (multi-level hierarchy).

    Queries:
    - Fetch all **main categories**: `Topics.objects.filter(parent__isnull=True)`
    - Fetch all **subcategories of a topic**: `some_topic.subcategories.all()`
    """

    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Topics"
        ordering = ["id"]

    def __str__(self):
        return self.name


class PriceLevel(models.Model):
    """
    Represents price tiers controlled by Admin.

    - **Only Admins** can create/edit price tiers.
    - Instructors must **choose from these preset prices**.
    - Courses store the **selected price directly**, instead of using an FK.
    - Supports **soft deletion** via `deleted_at`.

    Queries:
    - Fetch **active price levels**: `PriceLevel.objects.filter(deleted_at__isnull=True)`
    - Soft delete a price level: `some_price_level.delete()`
    """

    name = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["amount"]

    def __str__(self):
        return f"{self.name} - ₹{self.amount}"

    def delete(self, *args, **kwargs):
        """Soft delete instead of actual deletion."""
        self.deleted_at = timezone.now()
        self.save()


class Course(models.Model):
    """
    Represents an online course.

    - **Instructor**: The user who created the course.
    - **Topic**: The subject category for the course.
    - **Price**: Selected from `PriceLevel`, but stored as a direct decimal value.
    - **Status**: Controls course visibility (`Draft`, `Published`, etc.).
    - **Language**: The primary language of the course.

    Queries:
    - Get all **published courses**: `Course.objects.filter(status=Course.CourseStatus.PUBLISHED)`
    - Get all **courses by an instructor**: `Course.objects.filter(instructor=some_user)`
    """

    class CourseLevel(models.IntegerChoices):
        BEGINNER = 1, "Beginner"
        INTERMEDIATE = 2, "Intermediate"
        ADVANCED = 3, "Advanced"
        ALL_LEVEL = 4, "All Level"

    class CourseStatus(models.IntegerChoices):
        DRAFT = 0, "Draft"
        PENDING = 1, "Pending"
        PUBLISHED = 2, "Published"
        ARCHIVED = 3, "Archived"

    class LanguageChoices(models.TextChoices):
        ENGLISH = "EN", "English"
        SPANISH = "ES", "Spanish"
        FRENCH = "FR", "French"
        HINDI = "HI", "Hindi"
        OTHER = "OT", "Other"

    title = models.CharField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=255)
    instructor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="courses",
        null=True,
        blank=True,
    )
    topic = models.ForeignKey(
        Topics, on_delete=models.SET_NULL, related_name="courses", null=True, blank=True
    )
    description = models.TextField(blank=True, null=True)
    language = models.CharField(
        max_length=10, choices=LanguageChoices, default=LanguageChoices.ENGLISH
    )
    thumbnail = models.URLField(blank=True, null=True)
    trailer = models.URLField(blank=True, null=True)
    level = models.PositiveSmallIntegerField(
        choices=CourseLevel.choices, default=CourseLevel.BEGINNER
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.PositiveSmallIntegerField(
        choices=CourseStatus.choices, default=CourseStatus.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Courses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class CourseDetail(models.Model):
    """
    Stores additional course details (requirements, outcomes, target audiences).

    - **Requirement**: What students need before starting the course.
    - **Outcome**: What students will achieve after completing the course.
    - **Target Audience**: Who the course is designed for.

    Queries:
    - Get all **requirements** for a course: `course.details.filter(detail_type="requirement")`
    - Get all **outcomes** for a course: `course.details.filter(detail_type="outcome")`
    - Get all **target audiences** for a course: `course.details.filter(detail_type="target_audience")`
    """

    class DetailType(models.TextChoices):
        REQUIREMENT = "requirement", "Requirement"
        OUTCOME = "outcome", "Outcome"
        TARGET_AUDIENCE = "target_audience", "Target Audience"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="details")
    detail_type = models.CharField(
        max_length=20, choices=DetailType.choices, db_index=True
    )
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Course Details"
        ordering = ["detail_type"]

    def __str__(self):
        return f"{self.course.title} - {self.get_detail_type_display()}"





class Comments(models.Model):
    """
    Represents a comment or a reply in the discussion section of a course.

    Each comment is associated with a user and a course. Top-level comments have `parent=None`,
    while replies reference another comment via the `parent` field. The `is_instructor` flag
    automatically indicates if the commenter is the instructor of the course.

    Fields:
        user (ForeignKey): The user who posted the comment.
        course (ForeignKey): The course this comment is associated with.
        parent (ForeignKey): Optional. Points to another comment if this is a reply.
        comment (CharField): The text content of the comment.
        is_instructor (BooleanField): True if the commenter is the course instructor.
        created_at (DateTimeField): Timestamp when the comment was created.
        updated_at (DateTimeField): Timestamp when the comment was last updated.

    Meta:
        - Orders comments by newest first (`-created_at`).
        - Indexes on course, parent, and creation date for optimized lookups.

    Usage:
        - Retrieve top-level comments: `Comments.objects.filter(course=course, parent__isnull=True)`
        - Retrieve replies: `comment.replies.all()`
    """

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="comments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replies",
    )
    comment = models.CharField(max_length=500)
    is_instructor = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Comments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email}"
    
    def save(self, *args, **kwargs):
        if self.course and self.user:
            self.is_instructor = (self.course.instructor == self.user)
        super().save(*args, **kwargs)