from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Notification, NotificationPreference, NotificationType, NotificationTemplate
from .serializers import (
    NotificationSerializer, NotificationListSerializer, NotificationCreateSerializer,
    NotificationPreferenceSerializer, NotificationTypeSerializer,
    NotificationTemplateSerializer, BulkNotificationSerializer
)

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.
    
    Endpoints:
    - GET /notifications/ - List all notifications for current user
    - POST /notifications/ - Create a new notification (admin only)
    - GET /notifications/{id}/ - Retrieve a specific notification
    - PATCH /notifications/{id}/ - Update notification
    - DELETE /notifications/{id}/ - Delete notification
    - POST /notifications/mark_as_read/ - Mark notification as read
    - POST /notifications/mark_all_as_read/ - Mark all as read
    - GET /notifications/unread_count/ - Get unread count
    - GET /notifications/by_type/ - Filter by notification type
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        """Return notifications for the current user only"""
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by notification type if provided
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type__name=notification_type)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by course
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Mark a specific notification as read"""
        notification_id = request.data.get('notification_id')
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.mark_as_read()
            return Response(
                {'status': 'success', 'message': 'Notification marked as read'},
                status=status.HTTP_200_OK
            )
        except Notification.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read for current user"""
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response(
            {'status': 'success', 'marked_count': unread_count},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def mark_as_unread(self, request):
        """Mark a specific notification as unread"""
        notification_id = request.data.get('notification_id')
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.mark_as_unread()
            return Response(
                {'status': 'success', 'message': 'Notification marked as unread'},
                status=status.HTTP_200_OK
            )
        except Notification.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response(
            {'unread_count': count},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def unread_notifications(self, request):
        """Get all unread notifications"""
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')
        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def by_priority(self, request):
        """Get notifications filtered by priority"""
        priority = request.query_params.get('priority')
        if not priority:
            return Response(
                {'error': 'priority parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = self.get_queryset().filter(priority=priority)
        serializer = NotificationListSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def delete_all_read(self, request):
        """Delete all read notifications for current user"""
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()
        return Response(
            {'status': 'success', 'deleted_count': deleted_count},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_create(self, request):
        """
        Create notifications for multiple users (admin only).
        Requires: notification_type, users (list), title, message
        """
        serializer = BulkNotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            notification_type = NotificationType.objects.get(id=serializer.validated_data['notification_type'])
            users = User.objects.filter(id__in=serializer.validated_data['users'])
            
            notifications = []
            for user in users:
                notification = Notification(
                    notification_type=notification_type,
                    user=user,
                    title=serializer.validated_data['title'],
                    message=serializer.validated_data['message'],
                    description=serializer.validated_data.get('description', ''),
                    priority=serializer.validated_data['priority'],
                    action_url=serializer.validated_data.get('action_url', ''),
                    is_sent=True
                )
                notifications.append(notification)
            
            created = Notification.objects.bulk_create(notifications)
            return Response(
                {'status': 'success', 'created_count': len(created)},
                status=status.HTTP_201_CREATED
            )
        except NotificationType.DoesNotExist:
            return Response(
                {'error': 'NotificationType not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notification preferences.
    
    Endpoints:
    - GET /notification-preferences/ - Get current user's preferences
    - PATCH /notification-preferences/{id}/ - Update preferences
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer

    def get_queryset(self):
        """Return only current user's preference"""
        return NotificationPreference.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'patch'])
    def my_preferences(self, request):
        """Get or update current user's notification preferences"""
        try:
            preference = request.user.notification_preference
        except NotificationPreference.DoesNotExist:
            preference = NotificationPreference.objects.create(user=request.user)
        
        if request.method == 'PATCH':
            serializer = NotificationPreferenceSerializer(
                preference, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = NotificationPreferenceSerializer(preference)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notification types.
    List all available notification types.
    """
    permission_classes = [IsAuthenticated]
    queryset = NotificationType.objects.filter(is_active=True)
    serializer_class = NotificationTypeSerializer


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notification templates.
    """
    permission_classes = [IsAuthenticated]
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
