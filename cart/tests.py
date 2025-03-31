from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from cart.models import Cart
from courses.models import Course


class CartAPITestCase(APITestCase):
    """
    Test cases for Cart API using Django's unittest framework.
    """

    def setUp(self):
        """
        Setup test data before each test.
        """
        # Create Users
        self.student = User.objects.create_user(
            first_name="name",
            last_name="sam",
            email="student@example.com",
            username="student",
            password="student123",
            role=User.STUDENT,
        )
        self.instructor = User.objects.create_user(
            first_name="name",
            last_name="sam",
            email="instructor@example.com",
            username="instructor",
            password="instructor123",
            role=User.INSTRUCTOR,
        )
        self.admin = User.objects.create_superuser(
            first_name="name",
            last_name="sam",
            email="admin@example.com",
            username="admin",
            password="admin123",
        )

        # Generate Tokens
        self.student_token = str(RefreshToken.for_user(self.student).access_token)

        # Create Courses
        self.published_course = Course.objects.create(
            title="Django Advanced",
            subtitle="sample",
            status=Course.CourseStatus.PUBLISHED,
            price=499.00,
        )
        self.draft_course = Course.objects.create(
            title="Unpublished Course",
            subtitle="sample",
            status=Course.CourseStatus.DRAFT,
            price=499.00,
        )
        self.archived_course = Course.objects.create(
            title="Archived Course",
            subtitle="sample",
            status=Course.CourseStatus.ARCHIVED,
            price=499.00,
        )

        self.url = "/cart/"

    def authenticate(self):
        """
        Authenticate the student using JWT token.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")

    # ------------------------ Add to Cart Tests ------------------------

    def test_add_published_course_to_cart(self):
        """Test that a student can add a published course to their cart."""
        self.authenticate()
        response = self.client.post(self.url, {"course": self.published_course.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cart.objects.count(), 1)

    def test_cannot_add_unpublished_course_to_cart(self):
        """Test that a student cannot add a draft or archived course to their cart."""
        self.authenticate()
        response = self.client.post(self.url, {"course": self.draft_course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "This course is not available for purchase.", response.data["course"]
        )

    def test_cannot_add_same_course_twice(self):
        """Test that a student cannot add the same course to the cart twice."""
        self.authenticate()
        self.client.post(self.url, {"course": self.published_course.id})
        response = self.client.post(self.url, {"course": self.published_course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This course is already in your cart.", response.data["course"])

    # ------------------------ View Cart Tests ------------------------

    def test_view_cart_with_published_courses(self):
        """Test that students can see only published courses in their cart."""
        self.authenticate()
        Cart.objects.create(student=self.student, course=self.published_course)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["course_title"], self.published_course.title
        )

    def test_unpublished_course_not_visible_in_cart(self):
        """Test that unpublished courses are not visible in the cart."""
        self.authenticate()
        Cart.objects.create(student=self.student, course=self.archived_course)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_view_empty_cart(self):
        """Test that an empty cart returns an empty list."""
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    # ------------------------ Clear Cart Tests ------------------------

    def test_clear_cart(self):
        """Test that students can clear their cart."""
        self.authenticate()
        Cart.objects.create(student=self.student, course=self.published_course)
        response = self.client.delete(f"{self.url}clear/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cart.objects.count(), 0)

    def test_clear_empty_cart(self):
        """Test that clearing an empty cart returns a 'cart already empty' message."""
        self.authenticate()
        response = self.client.delete(f"{self.url}clear/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Your cart is already empty.")

    # ------------------------ Edge Cases ------------------------

    def test_invalid_course_id(self):
        """Test that an invalid course ID returns a 400 error."""
        self.authenticate()
        response = self.client.post(self.url, {"course": 999})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access cart endpoints."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
