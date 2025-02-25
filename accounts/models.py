from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
import random 
from django.utils.timezone import now, timedelta

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


class OtpVerification(models.Model):
    """Model representing OTP verification for user registration and password reset."""
    OTP_PURPOSES = (
        ("registration", "Registration"),
        ("password_reset", "Password Reset"),
        ("email_change", "Email Change"),
        ("other", "Other"),
    )
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="otp_verification")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    purpose = models.CharField(max_length=50, choices=OTP_PURPOSES, default="registration")

    class Meta:
        unique_together = ("user", "purpose")

    def save(self, *args, **kwargs):
        """Automatically generate otp and expiration time when creating a new entry"""

        if not self.otp:
            self.otp = str(random.randint(100000, 999999))
        if not self.expires_at:
            self.expires_at = now() + timedelta(minutes=10)

        super().save(*args, **kwargs) 

    def is_expired(self):
        """Check if the OTP has expired"""
        return now() > self.expires_at
    
    @classmethod
    def generate_otp(cls, user, purpose="registration"):
        """Create or update OTP for the given user and purpose"""
        otp_entry, created = cls.objects.update_or_create(
            user = user,
            purpose = purpose,
            defaults = {"otp": str(random.randint(100000, 999999)), "expires_at": now() + timedelta(minutes=10)}
        )
        return otp_entry.otp 
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp} (Purpose: {self.purpose}, Expires: {self.expires_at})"
        