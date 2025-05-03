from django.db import models

# Create your models here.
class Enrollments(models.Model):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    course = models.ForeignKey("courses.Course", on_delete=models.PROTECT, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_enrollment"
            )
        ]
        verbose_name_plural = "Enrollments"
        ordering = ["-enrolled_at"]