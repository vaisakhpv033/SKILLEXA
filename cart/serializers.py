from rest_framework import serializers

from courses.models import Course
from students.models import Enrollments

from .models import Cart, Wishlist


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    Provides course details within the cart
    """

    course_title = serializers.CharField(source="course.title", read_only=True)
    course_subtitle = serializers.CharField(source="course.subtitle", read_only=True)
    course_thumbnail = serializers.URLField(source="course.thumbnail", read_only=True)
    course_price = serializers.DecimalField(
        source="course.price", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            "id",
            "course",
            "course_title",
            "course_price",
            "course_thumbnail",
            "course_subtitle",
            "created_at",
            "updated_at",
        ]

    def validate_course(self, value):
        """
        Ensure a course exist and is not already in the cart
        """

        # check if the course exists and is published
        if not Course.objects.filter(
            id=value.id, status=Course.CourseStatus.PUBLISHED
        ).exists():
            raise serializers.ValidationError(
                "This course is not available for purchase."
            )

        student = self.context["request"].user

        # check if the course is already enrolled
        if Enrollments.objects.filter(
            student=student, course=value
        ).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")
    
        # check if the course is already in the cart
        if Cart.objects.filter(student=student, course=value).exists():
            raise serializers.ValidationError("This course is already in your cart.")

        return value





class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer for Wishlist model.
    Provides course details within the Wishlist
    """

    course_title = serializers.CharField(source="course.title", read_only=True)
    course_subtitle = serializers.CharField(source="course.subtitle", read_only=True)
    course_thumbnail = serializers.URLField(source="course.thumbnail", read_only=True)
    course_price = serializers.DecimalField(
        source="course.price", max_digits=10, decimal_places=2, read_only=True
    )
    course_level = serializers.CharField(source="course.get_level_display", read_only=True)
    topic_name = serializers.CharField(source="course.topic.name", read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "course",
            "course_title",
            "course_price",
            "course_thumbnail",
            "course_subtitle",
            "created_at",
            "updated_at",
            "course_level",
            "topic_name",
        ]

    def validate_course(self, value):
        """
        Ensure a course exist and is not already in the Wishlist
        """

        # check if the course exists and is published
        if not Course.objects.filter(
            id=value.id, status=Course.CourseStatus.PUBLISHED
        ).exists():
            raise serializers.ValidationError(
                "This course is not available for purchase."
            )

        student = self.context["request"].user

        # check if the course is already in the cart
        if Wishlist.objects.filter(student=student, course=value).exists():
            raise serializers.ValidationError("This course is already in your wishlist.")

        return value
