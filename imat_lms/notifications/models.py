from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Course

User = get_user_model()


class NotificationType(models.Model):
    """
    Notification type definitions.
    Allows categorizing notifications by type for filtering and preferences.
    """
    CATEGORY_CHOICES = [
        ('course', 'Course Updates'),
        ('assignment', 'Assignment & Tests'),
        ('reminder', 'Reminders & Alerts'),
        ('community', 'Community Activity'),
        ('payment', 'Payment Updates'),
        ('attendance', 'Attendance Updates'),
        ('system', 'System Messages'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Notification(models.Model):
    """
    Main notification model representing a single notification to a user.
    Stores notification details, read status, and metadata.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Basic notification info
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    description = models.TextField(blank=True, help_text="Additional details")
    
    # Priority and status
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_object_id = models.IntegerField(null=True, blank=True, help_text="ID of related object (assignment, post, etc.)")
    related_object_type = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Type of related object (e.g., 'assignment', 'discussion_post')"
    )
    
    # Action URLs
    action_url = models.CharField(max_length=500, blank=True, help_text="URL to navigate to when notification is clicked")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="Send at a specific time")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Notification expires after this date")
    
    # Delivery tracking
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def time_since_creation(self):
        """Get human-readable time since creation"""
        from django.utils.timesince import timesince
        return f"{timesince(self.created_at)} ago"


class NotificationPreference(models.Model):
    """
    User notification preferences - which types of notifications to receive and how.
    """
    DELIVERY_CHANNELS = [
        ('in_app', 'In App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Course notifications
    notify_new_course = models.BooleanField(default=True, help_text="Notify when new course is added")
    notify_course_updates = models.BooleanField(default=True, help_text="Notify about course updates")
    
    # Assignment notifications
    notify_new_assignment = models.BooleanField(default=True)
    notify_assignment_due = models.BooleanField(default=True)
    notify_assignment_graded = models.BooleanField(default=True)
    
    # Reminder notifications
    notify_reminders = models.BooleanField(default=True)
    notify_daily_learning = models.BooleanField(default=True)
    
    # Community notifications
    notify_community = models.BooleanField(default=True)
    notify_replies = models.BooleanField(default=True)
    
    # Delivery channels
    preferred_channels = models.JSONField(
        default=list, 
        help_text="List of preferred delivery channels",
        blank=True
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Notification Preferences - {self.user.email}"


class NotificationTemplate(models.Model):
    """
    Templates for generating consistent notification messages.
    Allows for easy customization and translation.
    """
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=100)
    title_template = models.CharField(max_length=255, help_text="Use {placeholders} for dynamic content")
    message_template = models.TextField(help_text="Use {placeholders} for dynamic content")
    description_template = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['notification_type', 'name']
        ordering = ['notification_type', 'name']

    def __str__(self):
        return f"{self.name} - {self.notification_type.name}"

    def render(self, context):
        """
        Render template with context variables.
        
        Args:
            context (dict): Dictionary with template variables
            
        Returns:
            dict: Rendered title, message, and description
        """
        return {
            'title': self.title_template.format(**context),
            'message': self.message_template.format(**context),
            'description': self.description_template.format(**context) if self.description_template else '',
        }
