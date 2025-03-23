from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils.timezone import now, timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from accounts.models import OtpVerification, User

class InstructorResetPasswordTestCase(APITestCase):
    """Unit tests for instructor password reset API"""

    def setUp(self):
        """Create test users and OTP before each test"""
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            username="instructor1",
            password="OldPass123",
            first_name="John",
            last_name="Doe",
            role=User.INSTRUCTOR,
            is_active=True,
        )

        self.student = User.objects.create_user(
            email="student@example.com",
            username="student1",
            password="OldPass123",
            first_name="Jane",
            last_name="Doe",
            role=User.STUDENT,
            is_active=True,
        )

        # Generate JWT tokens for authentication
        self.instructor_token = str(RefreshToken.for_user(self.instructor).access_token)
        self.student_token = str(RefreshToken.for_user(self.student).access_token)

        # Generate valid OTP for password reset
        self.otp = OtpVerification.objects.create(
            user=self.instructor,
            otp="654321",
            expires_at=now() + timedelta(minutes=5),
            purpose="password_reset",
        )

        self.api_url = reverse("instructor-reset-password")

    def test_successful_password_reset(self):
        """Test successful password reset for instructor"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")

        response = self.client.post(
            self.api_url,
            {
                "otp": "654321",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password Reset Successfully")

        # Ensure password is actually updated
        self.instructor.refresh_from_db()
        self.assertTrue(check_password("NewSecurePass123", self.instructor.password))

        # Ensure OTP is deleted after reset
        self.assertFalse(
            OtpVerification.objects.filter(
                user=self.instructor, purpose="password_reset"
            ).exists()
        )

    def test_invalid_otp(self):
        """Test password reset fails with incorrect OTP"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")

        response = self.client.post(
            self.api_url,
            {
                "otp": "000000",  # Wrong OTP
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("OTP is Invalid or Expired", response.data["otp"])

    def test_expired_otp(self):
        """Test password reset fails with expired OTP"""
        self.otp.expires_at = now() - timedelta(minutes=1)  # Expire the OTP
        self.otp.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")

        response = self.client.post(
            self.api_url,
            {
                "otp": "654321",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("OTP is Invalid or Expired", response.data["otp"])

    def test_password_mismatch(self):
        """Test password reset fails when passwords do not match"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")

        response = self.client.post(
            self.api_url,
            {
                "otp": "654321",
                "new_password": "NewSecurePass123",
                "confirm_password": "WrongPass123",  # Mismatched password
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data["password"])

    def test_non_instructor_cannot_reset_password(self):
        """Test students cannot reset passwords via instructor endpoint"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")

        response = self.client.post(
            self.api_url,
            {
                "otp": "654321",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_reset_password(self):
        """Test unauthenticated users cannot access the API"""
        response = self.client.post(
            self.api_url,
            {
                "otp": "654321",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_fields(self):
        """Test missing required fields in request"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")

        response = self.client.post(
            self.api_url,
            {
                "otp": "654321",
                "new_password": "NewSecurePass123",
                # Missing confirm_password
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)



class InstructorResetPasswordOTPTestCase(APITestCase):
    """ Unit tests for Instructor Reset Password OTP API """

    def setUp(self):
        """ Create test users before each test """
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            username="instructor1",
            password="InstructorPass123",
            first_name="John",
            last_name="Doe",
            role=User.INSTRUCTOR,
            is_active=True,
        )

        self.student = User.objects.create_user(
            email="student@example.com",
            username="student1",
            password="StudentPass123",
            first_name="Jane",
            last_name="Doe",
            role=User.STUDENT,
            is_active=True,
        )

        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="AdminPass123",
            first_name="Admin",
            last_name="User",
            is_active=True,
        )

        # Generate JWT tokens for authentication
        self.instructor_token = str(RefreshToken.for_user(self.instructor).access_token)
        self.student_token = str(RefreshToken.for_user(self.student).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

        self.otp_url = reverse("instructor-reset-otp")

    def authenticate_as_instructor(self):
        """ Helper method to authenticate as instructor """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.instructor_token}")

    def authenticate_as_student(self):
        """ Helper method to authenticate as student """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")

    def authenticate_as_admin(self):
        """ Helper method to authenticate as admin """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

    @patch("accounts.tasks.send_email.delay")
    def test_successful_otp_generation(self, mock_send_email):
        """ Instructor can successfully request OTP """
        self.authenticate_as_instructor()

        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "OTP sent to your email")

        # Ensure OTP is stored in the database
        self.assertTrue(OtpVerification.objects.filter(user=self.instructor, purpose="password_reset").exists())

        # Ensure Celery email task is triggered
        mock_send_email.assert_called_once()

    def test_unauthorized_user_cannot_request_otp(self):
        """ Unauthenticated users cannot request OTP """
        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_instructor_cannot_request_otp(self):
        """ Non-instructor users (students/admins) cannot request OTP """
        self.authenticate_as_student()

        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate_as_admin()
        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("accounts.tasks.send_email.delay")
    def test_throttle_limit_on_otp_request(self, mock_send_email):
        """ OTP request is rate-limited if sent too many times """
        self.authenticate_as_instructor()

        # Simulate sending multiple requests
        for _ in range(10):
            self.client.post(self.otp_url)

        # The last request should be throttled
        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("accounts.tasks.send_email.delay")
    def test_otp_is_regenerated_on_multiple_requests(self, mock_send_email):
        """ New OTP should be generated on multiple requests """
        self.authenticate_as_instructor()

        # Request OTP first time
        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp_1 = OtpVerification.objects.get(user=self.instructor, purpose="password_reset").otp

        # Request OTP again
        response = self.client.post(self.otp_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp_2 = OtpVerification.objects.get(user=self.instructor, purpose="password_reset").otp

        self.assertNotEqual(otp_1, otp_2)  # Ensure a new OTP is generated
