from django.db import models


class Cart(models.Model):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.email}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course_cart"
            )
        ]
        verbose_name_plural = "Cart"
        ordering = ["-created_at"]


class Wishlist(models.Model):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.email}"

    class Meta:
        unique_together = ["student", "course"]
        verbose_name_plural = "Wishlist"
        ordering = ["-created_at"]
