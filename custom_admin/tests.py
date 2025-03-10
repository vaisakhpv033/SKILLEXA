from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User


class AdminUserActionsTestCase(APITestCase):
    """Unit tests for Admin Blocking, Unblocking, and Activating Users"""

    def setUp(self):
        """Create test users before each test"""
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="adminuser",
            password="AdminPass123",
            first_name="Admin",
            last_name="User",
            is_active=True,
        )

        self.regular_user = User.objects.create_user(
            email="user@example.com",
            username="testuser",
            password="UserPass123",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_blocked=False,
        )

        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.user_token = str(RefreshToken.for_user(self.regular_user).access_token)

        self.block_url = f"/api/admin/users/{self.regular_user.id}/block/"
        self.unblock_url = f"/api/admin/users/{self.regular_user.id}/unblock/"
        self.activate_url = f"/api/admin/users/{self.regular_user.id}/activate/"
        self.non_existent_url = "/api/admin/users/9999/block/"  # ✅ Non-existent user

    def authenticate_as_admin(self):
        """Helper method to authenticate as admin"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

    def authenticate_as_user(self):
        """Helper method to authenticate as regular user"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")

    def test_admin_can_block_user(self):
        """Admin can successfully block a user"""
        self.authenticate_as_admin()

        response = self.client.patch(self.block_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            f"User {self.regular_user.username} has been blocked",
        )

        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_blocked)

    def test_admin_can_unblock_user(self):
        """Admin can successfully unblock a user"""
        self.regular_user.is_blocked = True
        self.regular_user.save()

        self.authenticate_as_admin()

        response = self.client.patch(self.unblock_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            f"User {self.regular_user.username} has been unblocked",
        )

        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_blocked)

    def test_admin_can_activate_user(self):
        """Admin can successfully activate a user"""
        self.regular_user.is_active = False
        self.regular_user.save()

        self.authenticate_as_admin()

        response = self.client.patch(self.activate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            f"User {self.regular_user.username} has been activated",
        )

        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)

    def test_non_admin_cannot_block_user(self):
        """Non-admin users cannot block other users"""
        self.authenticate_as_user()

        response = self.client.patch(self.block_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_unblock_user(self):
        """Non-admin users cannot unblock other users"""
        self.authenticate_as_user()

        response = self.client.patch(self.unblock_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_activate_user(self):
        """Non-admin users cannot activate other users"""
        self.authenticate_as_user()

        response = self.client.patch(self.activate_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_block_user(self):
        """Unauthenticated users cannot block users"""
        response = self.client.patch(self.block_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blocking_already_blocked_user_does_not_change_state(self):
        """Blocking an already blocked user should not change state"""
        self.regular_user.is_blocked = True
        self.regular_user.save()

        self.authenticate_as_admin()

        response = self.client.patch(self.block_url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )  # ✅ Still a success response

        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_blocked)  # ✅ Should still be blocked

    def test_unblocking_already_unblocked_user_does_not_change_state(self):
        """Unblocking an already unblocked user should not change state"""
        self.authenticate_as_admin()

        response = self.client.patch(self.unblock_url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )  # ✅ Still a success response

        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_blocked)  # ✅ Should still be unblocked

    def test_activating_already_active_user_does_not_change_state(self):
        """Activating an already active user should not change state"""
        self.authenticate_as_admin()

        response = self.client.patch(self.activate_url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )  # ✅ Still a success response

        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)  # ✅ Should still be active

    def test_blocking_non_existent_user_fails(self):
        """Trying to block a non-existent user should return 404"""
        self.authenticate_as_admin()

        response = self.client.patch(self.non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unblocking_non_existent_user_fails(self):
        """Trying to unblock a non-existent user should return 404"""
        self.authenticate_as_admin()

        response = self.client.patch(self.non_existent_url.replace("block", "unblock"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_activating_non_existent_user_fails(self):
        """Trying to activate a non-existent user should return 404"""
        self.authenticate_as_admin()

        response = self.client.patch(self.non_existent_url.replace("block", "activate"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
