from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, OtpVerification
import random
from unittest.mock import patch
from django.conf import settings
import jwt
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from datetime import datetime

class AuthenticationTestCase(APITestCase):
    """ Unit tests for JWT authentication (Login & Refresh) """

    def setUp(self):
        """ Setup test users before each test """
        self.login_url = reverse('login')
        self.refresh_url = "/accounts/token/refresh/"

        # Create a normal active user
        self.user = User.objects.create(
            email="user@example.com",
            username="user1",
            password=make_password("SecurePass123"),
            role=User.STUDENT,
            is_active=True,
            is_blocked=False,
        )

        # Create a blocked user
        self.blocked_user = User.objects.create(
            email="blocked@example.com",
            username="blocked_user",
            password=make_password("BlockedPass123"),
            role=User.STUDENT,
            is_active=True,
            is_blocked=True,  # Blocked user
        )

        # Create an inactive user (not activated)
        self.inactive_user = User.objects.create(
            email="inactive@example.com",
            username="inactive_user",
            password=make_password("InactivePass123"),
            role=User.STUDENT,
            is_active=False,  # Inactive user
            is_blocked=False,
        )

    # Login Test Cases (Obtain Token)
    
    def test_successful_login(self):
        """ Test successful login and token retrieval """
        response = self.client.post(self.login_url, {
            "email": "user@example.com",
            "password": "SecurePass123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_blocked_user_cannot_login(self):
        """ Test blocked users cannot log in (should return 403 Forbidden) """
        response = self.client.post(self.login_url, {
            "email": "blocked@example.com",
            "password": "BlockedPass123"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Your account has been blocked. Please contact support.")


    def test_invalid_credentials(self):
        """ Test login fails with invalid credentials """
        response = self.client.post(self.login_url, {
            "email": "user@example.com",
            "password": "WrongPass"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_login(self):
        """ Test inactive users cannot log in """
        response = self.client.post(self.login_url, {
            "email": "inactive@example.com",
            "password": "InactivePass123"
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Refresh Token Test Cases
    
    def test_successful_token_refresh(self):
        """ Test refreshing access token with a valid refresh token """
        refresh = str(RefreshToken.for_user(self.user))  # Generate refresh token
        response = self.client.post(self.refresh_url, {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_blocked_user_cannot_refresh_token(self):
        """ Test blocked users cannot refresh tokens (should return 403 Forbidden) """
        refresh = str(RefreshToken.for_user(self.blocked_user))  # Generate refresh token for blocked user
        response = self.client.post(self.refresh_url, {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Your account has been blocked. Please contact support.")

    def test_expired_refresh_token(self):
        """ Test expired refresh token cannot be used """
        refresh = RefreshToken.for_user(self.user)
        refresh.set_exp(from_time=datetime.utcnow() - timedelta(days=1))  # Expire the token immediately
        response = self.client.post(self.refresh_url, {"refresh": str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tampered_refresh_token(self):
        """ Test tampered refresh token fails """
        refresh = str(RefreshToken.for_user(self.user))[:-1] + "X"  # Modify last character
        response = self.client.post(self.refresh_url, {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_refresh_token(self):
        """ Test invalid refresh token fails """
        response = self.client.post(self.refresh_url, {"refresh": "invalidtoken123"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class UserRegistrationTest(APITestCase):
    def setUp(self):
        """ Setup test data before running each test """
        self.register_url = reverse("register")
        self.verify_otp_url = reverse("verify_otp")

    def test_user_registration_success(self):
        """ Test successful user registration """
        response = self.client.post(self.register_url, {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "1234567890",
            "password": "securepassword",
            "confirm_password": "securepassword",
            "role": 1
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(User.objects.first().is_active)  # User should be inactive before OTP verification
        self.assertEqual(OtpVerification.objects.count(), 1)  # OTP should be generated

    def test_user_registration_password_mismatch(self):
        """ Test registration failure when passwords don't match """
        response = self.client.post(self.register_url, {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword",
            "confirm_password": "wrongpassword"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)  # Error should mention password mismatch
        self.assertEqual(User.objects.count(), 0)  # No user should be created



class OTPVerificationTest(APITestCase):
    def setUp(self):
        """ Setup a test user and OTP entry before each test """
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="securepassword",
            is_active=False  # User is inactive until OTP verification
        )
        self.otp = str(random.randint(100000, 999999))
        self.otp_entry = OtpVerification.objects.create(
            user=self.user,
            otp=self.otp,
            purpose="registration"
        )
        self.verify_otp_url = "/accounts/register/verify/"

    def test_otp_verification_success(self):
        """ Test OTP verification and user activation """
        response = self.client.post(self.verify_otp_url, {
            "email": "test@example.com",
            "otp": self.otp,
            "purpose": "registration"
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)  # User should be activated
        self.assertEqual(OtpVerification.objects.count(), 0)  # OTP should be deleted after successful verification

    def test_otp_verification_expired(self):
        """ Test expired OTP scenario """
        self.otp_entry.expires_at = self.otp_entry.created_at  # Force OTP to expire
        self.otp_entry.save()

        response = self.client.post(self.verify_otp_url, {
            "email": "test@example.com",
            "otp": self.otp,
            "purpose": "registration"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)  # Should return "OTP has expired"

    def test_otp_verification_invalid(self):
        """ Test incorrect OTP scenario """
        response = self.client.post(self.verify_otp_url, {
            "email": "test@example.com",
            "otp": "000000",  # Wrong OTP
            "purpose": "registration"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)  # Should return "Invalid OTP"


class GoogleLoginTestCase(APITestCase):
    """ Unit Tests for Google Login API """

    def setUp(self):
        self.url = reverse("google-login") 
        self.valid_id_token = "VALID_GOOGLE_ID_TOKEN"
        self.valid_email = "testuser@example.com"
        self.valid_name = "Test User"
        self.google_user_id = "1234567890"  # Mocked Google unique user ID
        self.valid_google_response = {
            "sub": self.google_user_id,
            "email": self.valid_email,
            "name": self.valid_name
        }

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_google_login_success(self, mock_verify):
        """ Test successful Google login """
        mock_verify.return_value = self.valid_google_response  # Mock valid response from Google
        
        response = self.client.post(self.url, {
            "idToken": self.valid_id_token,
            "email": self.valid_email,
            "name": self.valid_name
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)  # Token should be in response
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["username"], self.google_user_id[:30])  # Check username consistency
        self.assertTrue(User.objects.filter(email=self.valid_email).exists())  # User should be created

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_google_login_existing_user(self, mock_verify):
        """ Test login with existing user """
        user = User.objects.create_user(email=self.valid_email, username=self.google_user_id[:30], first_name="Old", last_name="User")

        mock_verify.return_value = self.valid_google_response
        
        response = self.client.post(self.url, {
            "idToken": self.valid_id_token,
            "email": self.valid_email,
            "name": self.valid_name
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decode JWT tokens and compare claims 
        access_token = response.data["access"]
        decoded_token = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])

        self.assertEqual(decoded_token["username"], user.username)  # Username should match
        self.assertEqual(decoded_token["user_id"], user.id)

    def test_google_login_missing_id_token(self):
        """ Test missing ID token """
        response = self.client.post(self.url, {
            "email": self.valid_email,
            "name": self.valid_name
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("idToken", response.data)

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_google_login_email_mismatch(self, mock_verify):
        """ 
        Test Google login fails when email doesn't match ID token 
        """
        mock_verify.return_value = self.valid_google_response
        
        response = self.client.post(self.url, {
            "idToken": self.valid_id_token,
            "email": "wrong-email@example.com",  # Incorrect email
            "name": self.valid_name
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email mismatch", response.data["error"])

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_google_login_invalid_token(self, mock_verify):
        """
        Test invalid Google ID token 
        """
        mock_verify.side_effect = ValueError("Invalid token")  # Simulate invalid token

        response = self.client.post(self.url, {
            "idToken": "INVALID_TOKEN",
            "email": self.valid_email,
            "name": self.valid_name
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid token", response.data["error"])

   
class ResendOTPTestCase(APITestCase):
    """
    Test case for the OTP resend API
    """

    def setUp(self):
        """
        Set up test data before each test case
        """
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            password="TestPass123",
            first_name="Test",
            last_name="User",
            is_active=False,
        )

        self.url = reverse("resend-otp")
        self.valid_payload = {"email": self.user.email, "purpose": "registration"}


    @patch("accounts.models.OtpVerification.generate_otp")
    @patch("accounts.tasks.send_otp_email.delay")
    def resend_otp_success(self, mock_send_otp_email, mock_generate_otp):
        """
        Test successful otp resend
        """
        mock_generate_otp.return_value = "123456"

        response = self.client.post(self.url, self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent successfully")
        mock_generate_otp.assert_called_once_with(self.user, "registration")
        mock_send_otp_email.assert_called_once_with(self.user.email, "123456")

    
    def test_resend_otp_user_not_found(self):
        """
        Test failure when email is not registered
        """
        payload = {"email": "nonexistent@example.com", "purpose": "registration"}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "User not found")

    def test_resend_otp_missing_email(self):
        """
        Test failure when email is missing
        """

        payload = {"purpose": "registration"}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    @patch("accounts.models.OtpVerification.generate_otp")
    @patch("accounts.tasks.send_otp_email.delay")
    def test_resend_otp_missing_purpose(self, mock_send_otp_email, mock_generate_otp):
        """
        Test that when purpose is missing, it defaults to 'registration'
        """
        mock_generate_otp.return_value = "123456"
        
        payload = {"email": self.user.email}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent successfully")
        mock_generate_otp.assert_called_once_with(self.user, "registration")
        mock_send_otp_email.assert_called_once_with(self.user.email, "123456")

    def test_resend_otp_invalid_purpose(self):
        """
        Test failure when an invalid purpose is provided
        """

        payload = {"email": self.user.email, "purpose": "invalid purpose"}
        response = self.client.post(self.url, payload) 

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("purpose", response.data)



class RateLimitTestCase(APITestCase):
    """
    Test API rate limiting
    """

    def setUp(self):
        """
        setup a test user and generate JWT token
        """
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            password="TestPass123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.api_url = reverse("profile")
        self.api_url2 = reverse("login") # this url also contain custom throttling protection. 

    def test_authenticated_user_rate_limit(self):
        """Test rate limiting for authenticated users"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Send requests up to the rate limit
        for _ in range(2000):
            response = self.client.get(self.api_url)
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # One extra request should be blocked
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_unauthenticated_user_rate_limit(self):
        """Test rate limiting for unauthenticated users"""
        for _ in range(20):
            response = self.client.post(self.api_url2, {"email": "testuser@example.com", "password": "TestPass123"})
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # One extra request should be blocked
        response = self.client.post(self.api_url2, {"email": "testuser@example.com", "password": "TestPass123"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)



class ForgotPasswordTestCase(APITestCase):
    """
    Test Forgot Password OTP and Reset functionality, including throttling.
    """

    def setUp(self):
        """
        Setup test user.
        """
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            password="TestPass123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )

        self.otp_url = reverse("forgot-otp")  # URL for requesting OTP
        self.reset_url = reverse("forgot-password")  # URL for resetting password

        cache.clear() # clearing cache to reset throttling cache before each test

    def test_successful_otp_request(self):
        """ Test successful OTP request for password reset"""
        response = self.client.post(self.otp_url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent to your email")

    def test_otp_request_non_existent_email(self):
        """ Test OTP request with a non-existent email"""
        response = self.client.post(self.otp_url, {"email": "fake@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_otp_request_for_inactive_user(self):
        """ Test OTP request for an inactive user"""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(self.otp_url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_successful_password_reset(self):
        """ Test successful password reset using valid OTP"""
        otp = OtpVerification.generate_otp(self.user, "password_reset")

        response = self.client.post(self.reset_url, {
            "email": self.user.email,
            "otp": otp,
            "new_password": "NewSecurePass123",
            "confirm_password": "NewSecurePass123"
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password reset successful.")

        # Ensure password is actually changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePass123"))

    def test_password_reset_invalid_otp(self):
        """ Test password reset with an incorrect OTP"""
        response = self.client.post(self.reset_url, {
            "email": self.user.email,
            "otp": "999999",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)

    def test_password_reset_expired_otp(self):
        """ Test password reset with an expired OTP"""
        OtpVerification.objects.create(
            user=self.user,
            otp="123456",
            purpose="password_reset",
            expires_at=now() - timedelta(minutes=1)  # Expired OTP
        )

        response = self.client.post(self.reset_url, {
            "email": self.user.email,
            "otp": "123456",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)

    def test_password_reset_passwords_do_not_match(self):
        """ Test password reset with non-matching passwords"""
        otp = OtpVerification.generate_otp(self.user, "password_reset")

        response = self.client.post(self.reset_url, {
            "email": self.user.email,
            "otp": otp,
            "new_password": "NewPass123",
            "confirm_password": "WrongPass123"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_otp_request_throttling(self):
        """ Test OTP request throttling (max 5 per hour)"""
        for _ in range(5):  # Send 5 valid requests
            response = self.client.post(self.otp_url, {"email": self.user.email})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6th request should be rate-limited (HTTP 429)
        response = self.client.post(self.otp_url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_password_reset_throttling(self):
        """ Test password reset throttling"""
        otp = OtpVerification.generate_otp(self.user, "password_reset")

        for _ in range(5):  # Send 5 valid reset requests
            response = self.client.post(self.reset_url, {
                "email": self.user.email,
                "otp": otp,
                "new_password": "NewPass123",
                "confirm_password": "NewPass123"
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6th request should be rate-limited (HTTP 429)
        response = self.client.post(self.reset_url, {
            "email": self.user.email,
            "otp": otp,
            "new_password": "NewPass123",
            "confirm_password": "NewPass123"
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)