from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, NotificationPreference, NotificationType, NotificationTemplate

User = get_user_model()


class NotificationTypeSerializer(serializers.ModelSerializer):
    """Serializer for NotificationType"""
    
    class Meta:
        model = NotificationType
        fields = ['id', 'name', 'category', 'description', 'is_active']
        read_only_fields = ['id']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    notification_type_name = serializers.CharField(source='notification_type.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    time_since_creation = serializers.CharField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_name', 'user', 'user_email',
            'title', 'message', 'description', 'priority', 'is_read', 'read_at',
            'course', 'course_title', 'related_object_id', 'related_object_type',
            'action_url', 'created_at', 'updated_at', 'time_since_creation',
            'scheduled_for', 'expires_at', 'is_sent', 'sent_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'sent_at', 'read_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for notification lists"""
    notification_type_name = serializers.CharField(source='notification_type.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type_name', 'title', 'message',
            'priority', 'is_read', 'course_title', 'action_url',
            'created_at', 'time_since_creation'
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'notification_type', 'user', 'title', 'message', 'description',
            'priority', 'course', 'related_object_id', 'related_object_type',
            'action_url', 'scheduled_for', 'expires_at'
        ]

    def create(self, validated_data):
        """Create and return a new notification"""
        validated_data['is_sent'] = True
        return super().create(validated_data)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_email', 'notify_new_course', 'notify_course_updates',
            'notify_new_assignment', 'notify_assignment_due', 'notify_assignment_graded',
            'notify_reminders', 'notify_daily_learning', 'notify_community',
            'notify_replies', 'preferred_channels', 'quiet_hours_enabled',
            'quiet_hours_start', 'quiet_hours_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate"""
    notification_type_name = serializers.CharField(source='notification_type.name', read_only=True)

    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'notification_type', 'notification_type_name', 'name',
            'title_template', 'message_template', 'description_template',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for bulk notification creation"""
    notification_type = serializers.IntegerField()
    users = serializers.ListField(child=serializers.IntegerField())
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high', 'urgent'])
    course = serializers.IntegerField(required=False, allow_null=True)
    action_url = serializers.CharField(required=False, allow_blank=True)
