from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User, OtpVerification
import random


class UserRegistrationTest(APITestCase):
    def setUp(self):
        """ Setup test data before running each test """
        self.register_url = "/accounts/register/"
        self.verify_otp_url = "/accounts/register/verify/"

    def test_user_registration_success(self):
        """ ✅ Test successful user registration """
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
        """ ❌ Test registration failure when passwords don't match """
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
            is_active=False  # ✅ User is inactive until OTP verification
        )
        self.otp = str(random.randint(100000, 999999))
        self.otp_entry = OtpVerification.objects.create(
            user=self.user,
            otp=self.otp,
            purpose="registration"
        )
        self.verify_otp_url = "/accounts/register/verify/"

    def test_otp_verification_success(self):
        """ ✅ Test OTP verification and user activation """
        response = self.client.post(self.verify_otp_url, {
            "email": "test@example.com",
            "otp": self.otp,
            "purpose": "registration"
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)  # ✅ User should be activated
        self.assertEqual(OtpVerification.objects.count(), 0)  # ✅ OTP should be deleted after successful verification

    def test_otp_verification_expired(self):
        """ ❌ Test expired OTP scenario """
        self.otp_entry.expires_at = self.otp_entry.created_at  # Force OTP to expire
        self.otp_entry.save()

        response = self.client.post(self.verify_otp_url, {
            "email": "test@example.com",
            "otp": self.otp,
            "purpose": "registration"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)  # ✅ Should return "OTP has expired"

    def test_otp_verification_invalid(self):
        """ ❌ Test incorrect OTP scenario """
        response = self.client.post(self.verify_otp_url, {
            "email": "test@example.com",
            "otp": "000000",  # Wrong OTP
            "purpose": "registration"
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("otp", response.data)  # ✅ Should return "Invalid OTP"
