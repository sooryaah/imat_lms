"""
Serializers for community models.

Handles serialization of:
- Community Groups
- Discussion Posts
- Chat Messages
- Group Members
- Notifications
"""

from rest_framework import serializers
from .models import (
    CommunityGroup,
    GroupMember,
    DiscussionPost,
    PostReaction,
    ChatMessage,
    ChatMessageReadReceipt,
    Notification,
)
from accounts.models import CustomUser


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for display in community features"""
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'profile_image', 'profile_image_url', 'role']
        read_only_fields = fields

    def get_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.profile_image:
            return request.build_absolute_uri(obj.profile_image.url) if request else obj.profile_image.url
        return None


class GroupMemberSerializer(serializers.ModelSerializer):
    """Serializer for group members with user details"""
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = GroupMember
        fields = [
            'id', 'user', 'user_id', 'role', 'is_active',
            'joined_at', 'email_notifications', 'push_notifications'
        ]
        read_only_fields = ['id', 'user', 'joined_at']

    def validate_role(self, value):
        """Validate role based on user permissions"""
        request = self.context.get('request')
        if request and request.user.role != 'admin':
            if value != 'member':
                raise serializers.ValidationError(
                    "Only admins can assign moderator or instructor roles."
                )
        return value


class PostReactionSerializer(serializers.ModelSerializer):
    """Serializer for post reactions"""
    user = UserBasicSerializer(source='user', read_only=True)

    class Meta:
        model = PostReaction
        fields = ['id', 'reaction_type', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class DiscussionPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing discussion posts"""
    author = UserBasicSerializer(read_only=True)
    reactions_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionPost
        fields = [
            'id', 'title', 'author', 'created_at', 'updated_at',
            'view_count', 'reply_count', 'is_pinned', 'status',
            'reactions_count', 'user_reaction'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at',
            'view_count', 'reply_count'
        ]

    def get_reactions_count(self, obj):
        """Count reactions by type"""
        reactions = obj.reactions.values('reaction_type').annotate(
            count=serializers.Count('id')
        )
        return {r['reaction_type']: r['count'] for r in reactions}

    def get_user_reaction(self, obj):
        """Get current user's reaction if any"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.reaction_type if reaction else None
        return None


class DiscussionPostDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual discussion posts with nested replies"""
    author = UserBasicSerializer(read_only=True)
    author_id = serializers.IntegerField(write_only=True, required=False)
    replies = serializers.SerializerMethodField()
    reactions = PostReactionSerializer(many=True, read_only=True)
    reactions_summary = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionPost
        fields = [
            'id', 'community', 'author', 'author_id', 'title', 'content',
            'status', 'is_pinned', 'view_count', 'reply_count',
            'created_at', 'updated_at', 'replies', 'reactions',
            'reactions_summary', 'can_edit', 'can_delete',
            'flagged_for_review', 'moderation_notes'
        ]
        read_only_fields = [
            'id', 'community', 'author', 'created_at', 'updated_at',
            'view_count', 'reply_count', 'flagged_for_review',
            'moderation_notes'
        ]

    def get_replies(self, obj):
        """Get nested replies for this post"""
        replies = obj.replies.filter(is_deleted=False)
        return DiscussionPostListSerializer(replies, many=True, context=self.context).data

    def get_reactions_summary(self, obj):
        """Summarize reactions by type"""
        reactions = obj.reactions.values('reaction_type').annotate(
            count=serializers.Count('id')
        )
        return {r['reaction_type']: r['count'] for r in reactions}

    def get_can_edit(self, obj):
        """Check if user can edit this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False

    def get_can_delete(self, obj):
        """Check if user can delete this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user or request.user.is_staff
        return False


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for real-time chat messages"""
    sender = UserBasicSerializer(read_only=True)
    sender_id = serializers.IntegerField(write_only=True, required=False)
    attachment_url = serializers.SerializerMethodField()
    read_by_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'community', 'sender', 'sender_id', 'message',
            'message_type', 'attachment', 'attachment_url', 'attachment_type',
            'status', 'is_edited', 'edited_at', 'created_at',
            'read_at', 'read_by_count'
        ]
        read_only_fields = [
            'id', 'sender', 'status', 'created_at',
            'read_at', 'is_edited', 'edited_at'
        ]

    def get_attachment_url(self, obj):
        """Get full URL for attachment"""
        request = self.context.get('request')
        if obj.attachment:
            return request.build_absolute_uri(obj.attachment.url) if request else obj.attachment.url
        return None

    def get_read_by_count(self, obj):
        """Count how many people have read this message"""
        return obj.read_receipts.count()


class ChatMessageReadReceiptSerializer(serializers.ModelSerializer):
    """Serializer for message read receipts"""
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = ChatMessageReadReceipt
        fields = ['id', 'user', 'read_at']
        read_only_fields = fields


class ChatMessageDetailSerializer(ChatMessageSerializer):
    """Extended chat message serializer with read receipts"""
    read_receipts = ChatMessageReadReceiptSerializer(many=True, read_only=True)

    class Meta(ChatMessageSerializer.Meta):
        fields = ChatMessageSerializer.Meta.fields + ['read_receipts']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    actor = UserBasicSerializer(read_only=True)
    community_title = serializers.CharField(source='community.title', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'actor', 'community', 'community_title', 'post', 'post_title',
            'is_read', 'created_at', 'email_sent', 'push_sent'
        ]
        read_only_fields = [
            'id', 'notification_type', 'title', 'message',
            'actor', 'community', 'post', 'created_at',
            'email_sent', 'push_sent'
        ]


class CommunityGroupSerializer(serializers.ModelSerializer):
    """Serializer for community groups"""
    members_count = serializers.CharField(source='member_count', read_only=True)
    posts_count = serializers.CharField(source='post_count', read_only=True)
    user_role = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)
    banner_image_url = serializers.SerializerMethodField()

    class Meta:
        model = CommunityGroup
        fields = [
            'id', 'course', 'course_title', 'title', 'description',
            'visibility', 'banner_image', 'banner_image_url',
            'require_post_approval', 'members_count', 'posts_count',
            'user_role', 'is_member', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'course', 'members_count', 'posts_count',
            'created_at', 'updated_at'
        ]

    def get_user_role(self, obj):
        """Get current user's role in this community"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.members.filter(user=request.user).first()
            return membership.role if membership else None
        return None

    def get_is_member(self, obj):
        """Check if user is a member of this community"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(user=request.user, is_active=True).exists()
        return False

    def get_banner_image_url(self, obj):
        """Get full URL for banner image"""
        request = self.context.get('request')
        if obj.banner_image:
            return request.build_absolute_uri(obj.banner_image.url) if request else obj.banner_image.url
        return None


class CommunityGroupDetailSerializer(CommunityGroupSerializer):
    """Detailed serializer for community group with members list"""
    members = GroupMemberSerializer(many=True, read_only=True)
    recent_posts = serializers.SerializerMethodField()
    recent_messages = serializers.SerializerMethodField()

    class Meta(CommunityGroupSerializer.Meta):
        fields = CommunityGroupSerializer.Meta.fields + [
            'members', 'recent_posts', 'recent_messages'
        ]

    def get_recent_posts(self, obj):
        """Get 5 most recent discussion posts"""
        posts = obj.discussion_posts.filter(
            is_deleted=False,
            status='published'
        ).order_by('-created_at')[:5]
        return DiscussionPostListSerializer(posts, many=True, context=self.context).data

    def get_recent_messages(self, obj):
        """Get 20 most recent chat messages"""
        messages = obj.chat_messages.filter(is_deleted=False).order_by('-created_at')[:20]
        return ChatMessageSerializer(messages, many=True, context=self.context).data
