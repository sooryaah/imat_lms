from django.contrib import admin
from .models import NotificationType, Notification, NotificationPreference, NotificationTemplate


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('notification_type', 'user', 'title', 'message', 'description', 'priority')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_sent', 'sent_at')
        }),
        ('Related Objects', {
            'fields': ('course', 'related_object_id', 'related_object_type', 'action_url')
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notify_new_course', 'notify_new_assignment', 'notify_reminders']
    list_filter = ['notify_new_course', 'notify_new_assignment', 'notify_reminders', 'quiet_hours_enabled']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Course Notifications', {
            'fields': ('notify_new_course', 'notify_course_updates')
        }),
        ('Assignment Notifications', {
            'fields': ('notify_new_assignment', 'notify_assignment_due', 'notify_assignment_graded')
        }),
        ('Other Notifications', {
            'fields': ('notify_reminders', 'notify_daily_learning', 'notify_community', 'notify_replies')
        }),
        ('Delivery Preferences', {
            'fields': ('preferred_channels',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['name', 'title_template', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
