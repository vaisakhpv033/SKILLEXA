from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserProfileListSerializer, UserSerializer, OTPVerificationSerializer, GoogleLoginSerializer, OTPResendSerializer
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from google.oauth2 import id_token
from google.auth.transport import requests
from .models import User, OtpVerification
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.conf import settings
from .tasks import send_otp_email
from .throttles import LoginAttemptThrottle, OTPRequestThrottle

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API View for user login.
    
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = (LoginAttemptThrottle,)


class RegisterUserView(generics.CreateAPIView):
    """
    API View for user registration.
    Users will be created in an inactive state until they verify their OTP.

    """
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User created successfully. Please check your email for OTP verification."},
                status = status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountVerifyOTPView(generics.GenericAPIView):
    """
    API View for verifying OTP sent to user's email.

    """
    serializer_class = OTPVerificationSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User verified successfully!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(generics.GenericAPIView):
    """
    API endpoint to resend OTP for registration, password reset, or email change.
    """
    permission_classes = (AllowAny,)
    throttle_classes = (OTPRequestThrottle,)

    def post(self, request):
        serializer = OTPResendSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            purpose = serializer.validated_data["purpose"]

            try:
                user = User.objects.get(email=email)
                otp = OtpVerification.generate_otp(user, purpose)
                print(otp)
                # send otp 
                send_otp_email.delay(email, otp)
                return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    """ ✅ Class-Based View for Google Login """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        id_token_str = serializer.validated_data["idToken"]
        email = serializer.validated_data["email"]
        name = serializer.validated_data.get("name", "")
        role = serializer.validated_data.get("role", User.STUDENT)

        try:
            # Validate Google Client ID
            if not GOOGLE_CLIENT_ID:
                return Response({"error": "Google Client ID is not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verify Google ID Token
            idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), GOOGLE_CLIENT_ID)

            if idinfo["email"] != email:
                return Response({"error": "Email mismatch."}, status=status.HTTP_400_BAD_REQUEST)

            user_id = idinfo["sub"]

            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": user_id[:30],
                    "first_name": name.split()[0] if name else "",
                    "last_name": name.split()[1] if len(name.split()) > 1 else "",
                    "is_active": True,
                    "role": role,
                },
            )

            # Generate JWT tokens with custom claims
            refresh = RefreshToken.for_user(user)
            refresh["username"] = user.username
            refresh["role"] = user.role

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "username": user.username,
                    "role": user.role,
                    "created": created,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# to Retrieve user profile details 
class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileListSerializer

    def get_object(self):
        return self.request.user