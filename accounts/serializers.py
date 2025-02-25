from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, OtpVerification

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adding custom claims to the token
        token['username'] = user.username
        token['role'] = user.role
        
        return token
    
class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone_number', 'password', 'confirm_password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False},
            'phone_number': {'required': False}
            }
        
    def validate(self, data):
        """ Validate that password and confirm_password match """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            password=validated_data['password'],
            role=validated_data.get('role', User.STUDENT), 
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
        """ Validate if OTP is correct & not expired """
        try:
            user = User.objects.get(email=data["email"])
            otp_entry = OtpVerification.objects.get(user=user, purpose=data["purpose"])

            if otp_entry.is_expired():
                raise serializers.ValidationError({"otp": "OTP has expired. Please request a new one."})

            if otp_entry.otp != data["otp"]:
                raise serializers.ValidationError({"otp": "Invalid OTP. Please try again."})

        except (User.DoesNotExist, OtpVerification.DoesNotExist):
            raise serializers.ValidationError({"email": "Invalid email or OTP"})

        data["user"] = user
        return data

    def save(self):
        """ Activate user or allow password reset based on OTP purpose """
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
    
    
class UserProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'first_name', 'last_name', 'phone_number', 'profile_picture', 'designation', 'bio' ]

