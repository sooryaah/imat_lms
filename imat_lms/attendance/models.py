from django.db import models
from django.conf import settings
from courses.models import Course, Content


class AttendanceSession(models.Model):
    SESSION_TYPE_CHOICES = (
        ('live', 'Live Class'),
        ('module', 'Mandatory Module'),
        ('other', 'Other'),
    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_sessions')
    session_date = models.DateField()
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='live')
    is_required = models.BooleanField(default=True)
    # Optional direct link to a content that fulfills attendance automatically
    linked_content = models.ForeignKey(Content, null=True, blank=True, on_delete=models.SET_NULL, related_name='linked_sessions')
    title = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-session_date', '-id']
        indexes = [
            models.Index(fields=['course', 'session_date']),
        ]
        unique_together = [('course', 'session_date', 'title')]

    def __str__(self):
        base = self.title or f"Session on {self.session_date}"
        return f"{self.course.title} - {base}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    )

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    logged_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-logged_at']
        unique_together = [('session', 'user')]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.session} - {self.status}"