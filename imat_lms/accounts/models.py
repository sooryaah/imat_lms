from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import datetime

class CustomUser(AbstractUser):
    """
    Custom user model. Superusers can log in using username and password. Regular users use email and password.
    """
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('admin', 'Admin'),
        ('instructor', 'Instructor'),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others'),
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    course_name = models.CharField(max_length=100, blank=True)
    joining_month = models.CharField(max_length=20, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_instructor(self):
        return self.role == 'instructor'


class PasswordResetOTP(models.Model):
    """Stores a short OTP code for password reset tied to a user."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_otps')
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
 
    expiry_minutes = models.PositiveSmallIntegerField(default=15)

    class Meta:
        indexes = [models.Index(fields=['user', 'code'])]

    def is_expired(self):
        return timezone.now() > (self.created_at + datetime.timedelta(minutes=self.expiry_minutes))

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])
