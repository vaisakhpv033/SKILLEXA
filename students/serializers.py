from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from accounts.models import OtpVerification

from .models import Enrollments


class StudentResetPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """Validate OTP and password match"""
        request = self.context["request"]
        user = request.user

        otp = data.get("otp")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match"})

        try:
            otp_entry = OtpVerification.objects.get(user=user, purpose="password_reset")

            if otp_entry.is_expired() or otp_entry.otp != otp:
                raise serializers.ValidationError({"otp": "OTP is Invalid or Expired"})
        except OtpVerification.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP"})

        data["user"] = user
        return data

    def save(self):
        """Reset password after validation"""

        user = self.validated_data["user"]
        user.password = make_password(self.validated_data["new_password"])
        user.save()

        OtpVerification.objects.filter(user=user, purpose="password_reset").delete()

        return {"message": "Password reset successfully"}




class EnrolledCourseSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_subtitle = serializers.CharField(source="course.subtitle", read_only=True)
    course_thumbnail = serializers.URLField(source="course.thumbnail", read_only=True)
    course_price = serializers.DecimalField(source="course.price", max_digits=10, decimal_places=2, read_only=True)
    course_level = serializers.CharField(source="course.get_level_display", read_only=True)
    topic_name = serializers.CharField(source="course.topic.name", read_only=True)
    instructor_name = serializers.CharField(
        source="instructor.full_name", read_only=True
    )

    class Meta:
        model = Enrollments
        fields = ["id", "course", "course_title", "course_subtitle", "instructor_name", "course_level", "topic_name", "course_thumbnail", "course_price", "enrolled_at"]
