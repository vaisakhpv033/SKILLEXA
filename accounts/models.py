from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models

class UserManager(BaseUserManager):
    """Custom user manager for handling user creation."""

    def create_user(self, first_name, last_name, username, email, role=None, password=None, **extra_fields):
        """
        Create and return a regular user.

        Args:
            first_name (str): User's first name.
            last_name (str): User's last name.
            username (str): Unique username.
            email (str): Unique email address.
            password (str, optional): User's password. Defaults to None.
            role (int, optional): User role. Defaults to `User.STUDENT`.
            **extra_fields: Additional attributes.

        Raises:
            ValueError: If email or username is missing.

        Returns:
            User: The created user instance.
        """

        if not email:
            raise ValueError("User must have an email address")

        if not username:
            raise ValueError("User must have an username")
        
        if role is None:
            role = self.model.STUDENT


        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            role = role,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, first_name, last_name, username, email, password=None, **extra_fields):
        """
        Create and return a superuser with admin privileges.

        Args:
            first_name (str): Superuser's first name.
            last_name (str): Superuser's last name.
            username (str): Unique username.
            email (str): Unique email address.
            password (str, optional): Superuser's password. Defaults to None.
            **extra_fields: Additional attributes.

        Returns:
            User: The created superuser instance.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=self.model.ADMIN,
            **extra_fields,
        )
        return user

# validators
username_validator = RegexValidator(
    r'^[a-zA-Z0-9_]+$', 
    'Usernames can only contain letters, numbers and underscores.'
)

name_validator = RegexValidator(
    r'^[a-zA-Z\s]+$',
    'Enter a Valid name (Only alphabets and spaces)'
)


class User(AbstractBaseUser):
    """Custom User model with role-based authentication."""

    STUDENT = 1
    INSTRUCTOR = 2
    ADMIN = 3
    ROLE_CHOICE = (
        (STUDENT, "Student"),
        (INSTRUCTOR, "Instructor"),
        (ADMIN, "Admin")
    )

    first_name = models.CharField(max_length=50, validators=[name_validator])
    last_name = models.CharField(max_length=50, validators=[name_validator])
    username = models.CharField(max_length=50, unique=True, validators=[username_validator])
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=12, blank=True, null=True)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICE, default=STUDENT)
    profile_picture = models.URLField(blank=True, null=True)
    designation = models.CharField(max_length=250, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True


class SocialProfile(models.Model):
    """Model representing a user's social media profile."""
    
    user = models.ForeignKey("accounts.User", verbose_name="social_profiles", on_delete=models.CASCADE)
    platform = models.CharField(max_length=250)
    profile_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

