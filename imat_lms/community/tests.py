"""
Tests for community feature.

Unit and integration tests for:
- Community groups
- Discussion posts
- Chat messages
- Permissions and access control
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    CommunityGroup, GroupMember, DiscussionPost, PostReaction,
    ChatMessage, Notification
)
from courses.models import Course, Enrollment

User = get_user_model()


class CommunityGroupTests(TestCase):
    """Test cases for CommunityGroup model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            price=99.99
        )
        self.community = CommunityGroup.objects.create(
            course=self.course,
            title='Test Community',
            description='Test Community Description'
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_community_creation(self):
        """Test creating a community group"""
        self.assertEqual(self.community.title, 'Test Community')
        self.assertEqual(self.community.course, self.course)
        self.assertEqual(self.community.visibility, 'public')

    def test_update_member_count(self):
        """Test updating member count"""
        GroupMember.objects.create(
            community=self.community,
            user=self.user,
            role='member'
        )
        self.community.update_member_count()
        self.assertEqual(self.community.member_count, 1)

    def test_update_post_count(self):
        """Test updating post count"""
        DiscussionPost.objects.create(
            community=self.community,
            author=self.user,
            title='Test Post',
            content='Test Content'
        )
        self.community.update_post_count()
        self.assertEqual(self.community.post_count, 1)


class GroupMemberTests(TestCase):
    """Test cases for GroupMember model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            price=99.99
        )
        self.community = CommunityGroup.objects.create(
            course=self.course,
            title='Test Community'
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_group_member_creation(self):
        """Test creating a group member"""
        member = GroupMember.objects.create(
            community=self.community,
            user=self.user,
            role='member'
        )
        self.assertEqual(member.user, self.user)
        self.assertEqual(member.role, 'member')
        self.assertTrue(member.is_active)

    def test_unique_constraint(self):
        """Test that a user can only join a community once"""
        GroupMember.objects.create(
            community=self.community,
            user=self.user
        )
        with self.assertRaises(Exception):
            GroupMember.objects.create(
                community=self.community,
                user=self.user
            )

    def test_is_moderator(self):
        """Test is_moderator method"""
        member = GroupMember.objects.create(
            community=self.community,
            user=self.user,
            role='member'
        )
        self.assertFalse(member.is_moderator())
        
        member.role = 'moderator'
        self.assertTrue(member.is_moderator())


class DiscussionPostTests(TestCase):
    """Test cases for DiscussionPost model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            price=99.99
        )
        self.community = CommunityGroup.objects.create(
            course=self.course,
            title='Test Community'
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_discussion_post_creation(self):
        """Test creating a discussion post"""
        post = DiscussionPost.objects.create(
            community=self.community,
            author=self.user,
            title='Test Post',
            content='Test Content'
        )
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.status, 'published')
        self.assertFalse(post.is_deleted)

    def test_soft_delete(self):
        """Test soft deleting a post"""
        post = DiscussionPost.objects.create(
            community=self.community,
            author=self.user,
            title='Test Post',
            content='Test Content'
        )
        post.soft_delete()
        self.assertTrue(post.is_deleted)
        self.assertIsNotNone(post.deleted_at)

    def test_increment_view_count(self):
        """Test incrementing view count"""
        post = DiscussionPost.objects.create(
            community=self.community,
            author=self.user,
            title='Test Post',
            content='Test Content'
        )
        self.assertEqual(post.view_count, 0)
        post.increment_view_count()
        post.refresh_from_db()
        self.assertEqual(post.view_count, 1)


class ChatMessageTests(TestCase):
    """Test cases for ChatMessage model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            price=99.99
        )
        self.community = CommunityGroup.objects.create(
            course=self.course,
            title='Test Community'
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_chat_message_creation(self):
        """Test creating a chat message"""
        message = ChatMessage.objects.create(
            community=self.community,
            sender=self.user,
            message='Test Message'
        )
        self.assertEqual(message.message, 'Test Message')
        self.assertEqual(message.status, 'sent')
        self.assertFalse(message.is_deleted)

    def test_mark_as_read(self):
        """Test marking message as read"""
        message = ChatMessage.objects.create(
            community=self.community,
            sender=self.user,
            message='Test Message'
        )
        message.mark_as_read()
        message.refresh_from_db()
        self.assertEqual(message.status, 'read')
        self.assertIsNotNone(message.read_at)

    def test_edit_message(self):
        """Test editing a message"""
        message = ChatMessage.objects.create(
            community=self.community,
            sender=self.user,
            message='Original Message'
        )
        message.edit_message('Edited Message')
        message.refresh_from_db()
        self.assertEqual(message.message, 'Edited Message')
        self.assertTrue(message.is_edited)


class NotificationTests(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            price=99.99
        )
        self.community = CommunityGroup.objects.create(
            course=self.course,
            title='Test Community'
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.actor = User.objects.create_user(
            email='actor@example.com',
            username='actor',
            password='testpass123'
        )

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='new_post',
            title='New Post',
            message='A new post was created',
            actor=self.actor,
            community=self.community
        )
        self.assertEqual(notification.recipient, self.user)
        self.assertFalse(notification.is_read)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='new_post',
            title='New Post',
            message='A new post was created'
        )
        notification.mark_as_read()
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
