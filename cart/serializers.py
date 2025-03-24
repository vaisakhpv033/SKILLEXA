from rest_framework import serializers
from .models import Cart
from courses.models import Course 


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    Provides course details within the cart 
    """

    course_title = serializers.CharField(source='course.title', read_only=True)
    course_subtitle = serializers.CharField(source='course.subtitle', read_only=True)
    course_thumbnail = serializers.URLField(source='course.thumbnail', read_only=True)
    course_price = serializers.DecimalField(source='course.price', max_digits=10, decimal_places=2, read_only=True)


    class Meta:
        model =Cart 
        fields = ['id', 'course', 'course_title', 'course_price', 'course_thumbnail', 'course_subtitle', 'created_at', 'updated_at']

    def validate_course(self, value):
        """
        Ensure a course exist and is not already in the cart
        """

        # check if the course exists and is published
        if not Course.objects.filter(id=value.id, status=Course.CourseStatus.PUBLISHED).exists():
            raise serializers.ValidationError("This course is not available for purchase.")

        student = self.context['request'].user

        # check if the course is already in the cart
        if Cart.objects.filter(student=student, course=value).exists():
            raise serializers.ValidationError("This course is already in your cart.")
        
        return value

