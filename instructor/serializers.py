from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from accounts.models import OtpVerification


class InstructorResetPasswordSerializer(serializers.Serializer):
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
