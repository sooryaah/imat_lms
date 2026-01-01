"""
Admin configuration for community models.

Provides admin interface for managing:
- Community groups
- Discussion posts
- Chat messages
- Group members
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CommunityGroup, GroupMember, DiscussionPost,
    PostReaction, ChatMessage, ChatMessageReadReceipt, Notification
)


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'visibility', 'member_count', 'post_count', 'created_at']
    list_filter = ['visibility', 'require_post_approval', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['member_count', 'post_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description', 'visibility', 'banner_image')
        }),
        ('Moderation', {
            'fields': ('require_post_approval',)
        }),
        ('Statistics', {
            'fields': ('member_count', 'post_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'community', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__email', 'community__title']
    readonly_fields = ['joined_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    fieldsets = (
        ('Membership', {
            'fields': ('community', 'user', 'role', 'is_active')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'push_notifications')
        }),
        ('Meta', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ['title_truncated', 'community', 'author_email', 'status', 'is_pinned', 'view_count', 'reply_count', 'created_at']
    list_filter = ['status', 'is_pinned', 'flagged_for_review', 'created_at']
    search_fields = ['title', 'content', 'author__email', 'community__title']
    readonly_fields = ['view_count', 'reply_count', 'created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('community', 'author', 'title', 'content', 'parent_post')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_pinned', 'is_deleted')
        }),
        ('Moderation', {
            'fields': ('flagged_for_review', 'moderation_notes')
        }),
        ('Statistics', {
            'fields': ('view_count', 'reply_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Title'
    
    def author_email(self, obj):
        return obj.author.email if obj.author else 'Deleted'
    author_email.short_description = 'Author'


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user_email', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['post__title', 'user__email']
    readonly_fields = ['created_at']
    
    def post_title(self, obj):
        return obj.post.title[:50]
    post_title.short_description = 'Post'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['message_preview', 'community', 'sender_email', 'message_type', 'status', 'created_at']
    list_filter = ['message_type', 'status', 'is_deleted', 'created_at']
    search_fields = ['message', 'sender__email', 'community__title']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at', 'is_edited', 'edited_at']
    
    fieldsets = (
        ('Message', {
            'fields': ('community', 'sender', 'message', 'message_type')
        }),
        ('Attachment', {
            'fields': ('attachment', 'attachment_type'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'is_deleted')
        }),
        ('Editing', {
            'fields': ('is_edited', 'edited_at'),
            'classes': ('collapse',)
        }),
        ('Replies', {
            'fields': ('reply_to',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        preview = obj.message[:50]
        if len(obj.message) > 50:
            preview += '...'
        return preview
    message_preview.short_description = 'Message'
    
    def sender_email(self, obj):
        return obj.sender.email if obj.sender else 'Deleted'
    sender_email.short_description = 'Sender'


@admin.register(ChatMessageReadReceipt)
class ChatMessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'user_email', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__email', 'message__id']
    readonly_fields = ['read_at']
    
    def message_id(self, obj):
        return f"Message #{obj.message.id}"
    message_id.short_description = 'Message'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_type_badge', 'recipient_email', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'email_sent', 'push_sent', 'created_at']
    search_fields = ['title', 'message', 'recipient__email', 'actor__email']
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        ('Notification', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Related Objects', {
            'fields': ('actor', 'community', 'post', 'chat_message'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Delivery', {
            'fields': ('email_sent', 'push_sent'),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def notification_type_badge(self, obj):
        colors = {
            'new_post': 'blue',
            'new_reply': 'green',
            'new_message': 'purple',
            'new_mention': 'orange',
            'post_approved': 'green',
            'post_rejected': 'red',
            'moderator_action': 'red',
        }
        color = colors.get(obj.notification_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'
    
    def recipient_email(self, obj):
        return obj.recipient.email
    recipient_email.short_description = 'Recipient'
