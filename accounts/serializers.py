from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OtpVerification, User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT login serializer that prevents blocked users from getting tokens"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adding custom claims to the token
        token["username"] = user.username
        token["role"] = user.role

        return token

    def validate(self, attrs):
        """Check if user is blocked before generating token"""
        data = super().validate(attrs)
        user = self.user

        if user.is_blocked:
            raise PermissionDenied(
                "Your account has been blocked. Please contact support."
            )

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Custom JWT refresh serializer to prevent blocked users from refreshing tokens"""

    def validate(self, attrs):
        """Override refresh logic to check if the user is blocked"""

        # get the refresh token from the request and decode it
        refresh_token = attrs["refresh"]
        refresh = RefreshToken(refresh_token)
        user_id = refresh.payload.get("user_id")

        try:
            user = User.objects.get(id=user_id)
            if user.is_blocked:
                raise PermissionDenied(
                    "Your account has been blocked. Please contact support."
                )
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "User does not exist"})

        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "confirm_password",
            "role",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "role": {"required": False},
            "phone_number": {"required": False},
        }

    def validate(self, data):
        """Validate that password and confirm_password match"""
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone_number=validated_data.get("phone_number", ""),
            password=validated_data["password"],
            role=validated_data.get("role", User.STUDENT),
        )

        user.is_active = False
        user.save()

        # Generate and send OTP asynchronously via Celery
        from .tasks import send_otp_email

        otp = OtpVerification.generate_otp(user, purpose="registration")
        print(otp)

        send_otp_email.delay(user.email, otp)

        return user


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=OtpVerification.OTP_PURPOSES)

    def validate(self, data):
        """Validate if OTP is correct & not expired"""
        try:
            user = User.objects.get(email=data["email"])
            otp_entry = OtpVerification.objects.get(user=user, purpose=data["purpose"])

            if otp_entry.is_expired():
                raise serializers.ValidationError(
                    {"otp": "OTP has expired. Please request a new one."}
                )

            if otp_entry.otp != data["otp"]:
                raise serializers.ValidationError(
                    {"otp": "Invalid OTP. Please try again."}
                )

        except (User.DoesNotExist, OtpVerification.DoesNotExist):
            raise serializers.ValidationError({"email": "Invalid email or OTP"})

        data["user"] = user
        return data

    def save(self):
        """Activate user or allow password reset based on OTP purpose"""
        user = self.validated_data["user"]
        purpose = self.validated_data["purpose"]

        if purpose == "registration":
            user.is_active = True
            user.save()
        elif purpose == "password_reset":
            return {"message": "OTP verified. Proceed to reset password."}
        elif purpose == "email_change":
            return {"message": "OTP verified. Proceed with email change."}

        # Delete OTP after successful verification
        OtpVerification.objects.filter(user=user, purpose=purpose).delete()

        return {"message": "User verified successfully!"}


class OTPResendSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(
        choices=OtpVerification.OTP_PURPOSES, default="registration"
    )


class GoogleLoginSerializer(serializers.Serializer):
    idToken = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.IntegerField(required=False, allow_null=True)


class ForgotPasswordOtpSerializer(serializers.Serializer):
    """Serializer for requesting a password reset via OTP"""

    email = serializers.EmailField()

    def validate(self, data):
        """Check if email exists before sending OTP"""
        if not User.objects.filter(email=data["email"], is_active=True).exists():
            raise serializers.ValidationError(
                {"email": "No active account found with this email"}
            )
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password after OTP verification"""

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validate Otp and password matching"""
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        try:
            user = User.objects.get(email=data["email"])
            otp_entry = OtpVerification.objects.get(user=user, purpose="password_reset")

            if otp_entry.is_expired():
                raise serializers.ValidationError(
                    {"otp": "OTP expired request a new one"}
                )

            if otp_entry.otp != data["otp"]:
                raise serializers.ValidationError({"otp": "Invalid OTP"})
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})
        except OtpVerification.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid Otp"})
        return data

    def save(self):
        """
        Update Password and delete OTP after successful verification
        """
        user = User.objects.get(email=self.validated_data["email"])
        user.password = make_password(self.validated_data["new_password"])
        user.save()

        OtpVerification.objects.filter(user=user, purpose="password_reset").delete()
        return user


class UserProfileListSerializer(serializers.ModelSerializer):
    # prevents users from changing email and role
    email = serializers.EmailField(read_only=True)
    role = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "phone_number",
            "profile_picture",
            "designation",
            "bio",
        ]
