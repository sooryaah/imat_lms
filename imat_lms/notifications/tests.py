from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Course
from .models import Notification, NotificationType, NotificationPreference, NotificationTemplate

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='student'
        )
        self.notification_type = NotificationType.objects.create(
            name='test_notification',
            category='course',
            description='Test notification'
        )

    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            notification_type=self.notification_type,
            user=self.user,
            title='Test Notification',
            message='This is a test notification'
        )
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            notification_type=self.notification_type,
            user=self.user,
            title='Test',
            message='Test message'
        )
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_as_unread(self):
        """Test marking notification as unread"""
        notification = Notification.objects.create(
            notification_type=self.notification_type,
            user=self.user,
            title='Test',
            message='Test message',
            is_read=True,
            read_at=timezone.now()
        )
        notification.mark_as_unread()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)


class NotificationPreferenceTest(TestCase):
    """Test cases for NotificationPreference model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_create_preference(self):
        """Test creating notification preference"""
        preference = NotificationPreference.objects.create(user=self.user)
        self.assertTrue(preference.notify_new_course)
        self.assertTrue(preference.notify_new_assignment)

    def test_update_preference(self):
        """Test updating notification preference"""
        preference = NotificationPreference.objects.create(user=self.user)
        preference.notify_new_course = False
        preference.save()
        
        refreshed = NotificationPreference.objects.get(user=self.user)
        self.assertFalse(refreshed.notify_new_course)


class NotificationSignalTest(TestCase):
    """Test signal handlers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='testpass123',
            role='student'
        )
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            username='instructor',
            password='testpass123',
            role='instructor'
        )

    def test_user_preference_created_on_signup(self):
        """Test that notification preference is created when user is created"""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            username='newuser',
            password='testpass123',
            role='student'
        )
        self.assertTrue(hasattr(new_user, 'notification_preference'))
