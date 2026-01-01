"""
Community models for course discussions and real-time messaging.

This module defines the core models for:
- CommunityGroup: Course-specific discussion groups
- DiscussionPost: Threaded discussions within groups
- ChatMessage: Real-time chat messages using WebSockets
- GroupMember: Membership and roles within groups
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course, Enrollment


class CommunityGroup(models.Model):
    """
    Represents a community/discussion group tied to a course.
    Allows students and instructors to collaborate and discuss course content.
    """
    VISIBILITY_CHOICES = [
        ('public', 'Public - Visible to all enrolled students'),
        ('private', 'Private - Instructor only'),
        ('instructor_moderated', 'Instructor Moderated'),
    ]

    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='community_group')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    banner_image = models.ImageField(upload_to='community_banners/', null=True, blank=True)
    
    # Moderation
    require_post_approval = models.BooleanField(
        default=False,
        help_text="If True, posts must be approved by instructor before publishing"
    )
    
    # Members and activity
    member_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Community Groups'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['course', 'visibility']),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def update_member_count(self):
        """Update the member count for this community"""
        self.member_count = self.members.filter(is_active=True).count()
        self.save(update_fields=['member_count'])

    def update_post_count(self):
        """Update the post count for this community"""
        self.post_count = self.discussion_posts.filter(is_deleted=False).count()
        self.save(update_fields=['post_count'])


class GroupMember(models.Model):
    """
    Represents membership in a community group with role-based permissions.
    """
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('instructor', 'Instructor'),
    ]

    community = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    class Meta:
        unique_together = ['community', 'user']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['community', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.community.title} ({self.role})"

    def is_instructor(self):
        """Check if user is instructor for the related course"""
        return self.user.role == 'instructor' or self.role == 'instructor'

    def is_moderator(self):
        """Check if user is moderator or instructor"""
        return self.role in ['moderator', 'instructor']


class DiscussionPost(models.Model):
    """
    Represents a discussion thread/post in a community group.
    Supports nested replies and markdown formatting.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    community = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='discussion_posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='discussion_posts')
    
    # Content
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    
    # Threading
    parent_post = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='replies'
    )
    
    # Metadata
    is_pinned = models.BooleanField(default=False, help_text="Pinned posts appear at top")
    is_deleted = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    
    # Moderation
    flagged_for_review = models.BooleanField(default=False)
    moderation_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['community', 'status']),
            models.Index(fields=['author']),
            models.Index(fields=['is_pinned', 'created_at']),
        ]
        verbose_name_plural = 'Discussion Posts'

    def __str__(self):
        return f"{self.community.title} - {self.title[:50]}"

    def soft_delete(self):
        """Soft delete a post (mark as deleted without removing from DB)"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def increment_view_count(self):
        """Increment view counter"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def update_reply_count(self):
        """Update the reply count"""
        self.reply_count = self.replies.filter(is_deleted=False).count()
        self.save(update_fields=['reply_count'])


class PostReaction(models.Model):
    """
    Represents reactions (likes, reactions) to discussion posts.
    """
    REACTION_TYPES = [
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('helpful', '👌 Helpful'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Sad'),
    ]

    post = models.ForeignKey(DiscussionPost, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user', 'reaction_type']
        indexes = [
            models.Index(fields=['post', 'reaction_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.reaction_type} - {self.post.title[:30]}"


class ChatMessage(models.Model):
    """
    Represents real-time chat messages in a community group.
    Uses WebSockets (Django Channels) for real-time delivery.
    """
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]

    community = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='chat_messages_sent')
    
    message = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=[('text', 'Text'), ('image', 'Image'), ('file', 'File'), ('system', 'System')],
        default='text'
    )
    
    # For image/file uploads
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    attachment_type = models.CharField(
        max_length=20,
        choices=[('image', 'Image'), ('document', 'Document'), ('video', 'Video')],
        null=True,
        blank=True
    )
    
    # Message status for tracking delivery
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    
    # Replies to other messages
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Editing
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Deletion
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['community', 'created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['status']),
        ]
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        return f"{self.sender.email} - {self.community.title} - {self.created_at}"

    def mark_as_read(self):
        """Mark message as read"""
        if self.status != 'read':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])

    def mark_as_delivered(self):
        """Mark message as delivered"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.save(update_fields=['status'])

    def soft_delete(self):
        """Soft delete a message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def edit_message(self, new_message):
        """Edit an existing message"""
        self.message = new_message
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['message', 'is_edited', 'edited_at'])


class ChatMessageReadReceipt(models.Model):
    """
    Tracks read status of messages by individual users.
    Useful for showing "read by X people" indicators.
    """
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['message']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.message.id}"


class Notification(models.Model):
    """
    Stores notifications for community activities.
    Supports in-app, email, and push notifications.
    """
    NOTIFICATION_TYPES = [
        ('new_post', 'New Discussion Post'),
        ('new_reply', 'Reply to Your Post'),
        ('new_message', 'Direct Message'),
        ('new_mention', 'You Were Mentioned'),
        ('post_approved', 'Your Post Was Approved'),
        ('post_rejected', 'Your Post Was Rejected'),
        ('moderator_action', 'Moderator Action'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # Related objects
    community = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(DiscussionPost, on_delete=models.CASCADE, null=True, blank=True)
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notifications_created')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.recipient.email} - {self.notification_type}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
