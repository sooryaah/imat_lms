"""
Views for community features.

Implements REST API endpoints for:
- Community groups management
- Discussion posts (create, read, update, delete)
- Chat messages with WebSocket support
- Group member management
- Notifications
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, F
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    CommunityGroup, GroupMember, DiscussionPost, PostReaction,
    ChatMessage, ChatMessageReadReceipt, Notification
)
from .serializers import (
    CommunityGroupSerializer, CommunityGroupDetailSerializer,
    GroupMemberSerializer, DiscussionPostListSerializer,
    DiscussionPostDetailSerializer, PostReactionSerializer,
    ChatMessageSerializer, ChatMessageDetailSerializer,
    NotificationSerializer
)
from .permissions import (
    IsCommunityMember, IsCommunityInstructor, CanEditOwnPost,
    CanDeleteOwnPost, CanModeratePost, IsEnrolledInCourse, CanJoinCommunity
)
from courses.models import Enrollment
from django.db import transaction


class StandardPagination(PageNumberPagination):
    """Standard pagination for list endpoints"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommunityGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing community groups.
    
    Endpoints:
    - GET /api/community-groups/ - List all community groups
    - POST /api/community-groups/ - Create new group (admin only)
    - GET /api/community-groups/{id}/ - Get group details
    - POST /api/community-groups/{id}/join/ - Join a group
    - POST /api/community-groups/{id}/leave/ - Leave a group
    - GET /api/community-groups/{id}/members/ - List group members
    - POST /api/community-groups/{id}/posts/ - Create discussion post
    - GET /api/community-groups/{id}/posts/ - List discussion posts
    - GET /api/community-groups/{id}/messages/ - List chat messages
    """
    
    queryset = CommunityGroup.objects.all()
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, list uses basic serializer"""
        if self.action == 'retrieve':
            return CommunityGroupDetailSerializer
        return CommunityGroupSerializer

    def get_queryset(self):
        """Filter communities based on user enrollment and role"""
        user = self.request.user
        
        # Admins can see all communities
        if user.is_staff or user.is_superuser:
            return CommunityGroup.objects.all()
        
        # Regular users see only communities for courses they're enrolled in
        enrolled_courses = Enrollment.objects.filter(
            user=user,
            is_active=True
        ).values_list('course_id', flat=True)
        
        return CommunityGroup.objects.filter(
            Q(course_id__in=enrolled_courses) | Q(members__user=user)
        ).distinct()

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a community group"""
        community = self.get_object()
        
        # Check if user is enrolled in the course
        permission = CanJoinCommunity()
        if not permission.has_object_permission(request, self, community):
            return Response(
                {'detail': 'You must be enrolled in the course to join this community.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create membership
        membership, created = GroupMember.objects.get_or_create(
            community=community,
            user=request.user,
            defaults={'role': 'member', 'is_active': True}
        )
        
        if not created and not membership.is_active:
            membership.is_active = True
            membership.save()
            created = True
        
        if created:
            community.update_member_count()
            return Response(
                {'detail': 'Successfully joined the community.'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'detail': 'You are already a member of this community.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a community group"""
        community = self.get_object()
        
        try:
            membership = GroupMember.objects.get(community=community, user=request.user)
            membership.is_active = False
            membership.save()
            community.update_member_count()
            return Response(
                {'detail': 'Successfully left the community.'},
                status=status.HTTP_200_OK
            )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'You are not a member of this community.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List active members of a community"""
        community = self.get_object()
        members = community.members.filter(is_active=True)
        
        serializer = GroupMemberSerializer(
            members,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def posts(self, request, pk=None):
        """List or create discussion posts in a community"""
        community = self.get_object()
        
        # Check membership
        if not community.members.filter(user=request.user, is_active=True).exists():
            return Response(
                {'detail': 'You must be a member of this community.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            posts = community.discussion_posts.filter(
                is_deleted=False,
                status='published'
            ).order_by('-is_pinned', '-created_at')
            
            page = self.paginate_queryset(posts)
            if page is not None:
                serializer = DiscussionPostListSerializer(
                    page,
                    many=True,
                    context={'request': request}
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = DiscussionPostListSerializer(
                posts,
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = DiscussionPostDetailSerializer(
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                post = serializer.save(
                    community=community,
                    author=request.user,
                    status='published'
                )
                community.update_post_count()
                return Response(
                    DiscussionPostDetailSerializer(
                        post,
                        context={'request': request}
                    ).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get recent chat messages in a community"""
        community = self.get_object()
        
        # Check membership
        if not community.members.filter(user=request.user, is_active=True).exists():
            return Response(
                {'detail': 'You must be a member of this community.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = community.chat_messages.filter(
            is_deleted=False
        ).order_by('-created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = ChatMessageSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = ChatMessageSerializer(
            messages,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class DiscussionPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing discussion posts.
    
    Endpoints:
    - GET /api/posts/ - List posts
    - POST /api/posts/ - Create post
    - GET /api/posts/{id}/ - Get post details
    - PUT /api/posts/{id}/ - Update post
    - DELETE /api/posts/{id}/ - Delete post
    - POST /api/posts/{id}/react/ - Add reaction
    - POST /api/posts/{id}/approve/ - Approve post (moderator only)
    """
    
    queryset = DiscussionPost.objects.filter(is_deleted=False)
    serializer_class = DiscussionPostDetailSerializer
    permission_classes = [IsAuthenticated, IsCommunityMember]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Only show published posts for regular users"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return self.queryset
        
        return self.queryset.filter(status='published')

    def retrieve(self, request, *args, **kwargs):
        """Get post details and increment view count"""
        instance = self.get_object()
        instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update post with permission check"""
        instance = self.get_object()
        permission = CanEditOwnPost()
        
        if not permission.has_object_permission(request, self, instance):
            return Response(
                {'detail': 'You do not have permission to edit this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete post with permission check"""
        instance = self.get_object()
        permission = CanDeleteOwnPost()
        
        if not permission.has_object_permission(request, self, instance):
            return Response(
                {'detail': 'You do not have permission to delete this post.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add or update reaction to a post"""
        post = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        if not reaction_type:
            return Response(
                {'detail': 'reaction_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reaction, created = PostReaction.objects.get_or_create(
            post=post,
            user=request.user,
            reaction_type=reaction_type
        )
        
        serializer = PostReactionSerializer(reaction)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending post (moderator only)"""
        post = self.get_object()
        permission = CanModeratePost()
        
        if not permission.has_object_permission(request, self, post):
            return Response(
                {'detail': 'You do not have permission to moderate posts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if post.status != 'pending_approval':
            return Response(
                {'detail': 'This post is not pending approval.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post.status = 'published'
        post.save()
        
        return Response({'detail': 'Post approved.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a pending post with notes (moderator only)"""
        post = self.get_object()
        permission = CanModeratePost()
        
        if not permission.has_object_permission(request, self, post):
            return Response(
                {'detail': 'You do not have permission to moderate posts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if post.status != 'pending_approval':
            return Response(
                {'detail': 'This post is not pending approval.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post.status = 'draft'
        post.moderation_notes = request.data.get('notes', '')
        post.save()
        
        return Response({'detail': 'Post rejected.'}, status=status.HTTP_200_OK)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat messages.
    
    Note: Real-time messaging uses WebSockets (Django Channels).
    This provides REST endpoints for:
    - Fetching message history
    - Editing messages
    - Deleting messages
    - Marking as read
    
    Endpoints:
    - GET /api/chat-messages/ - List messages
    - POST /api/chat-messages/ - Send message
    - PUT /api/chat-messages/{id}/ - Edit message
    - DELETE /api/chat-messages/{id}/ - Delete message
    - POST /api/chat-messages/{id}/mark-as-read/ - Mark as read
    """
    
    queryset = ChatMessage.objects.filter(is_deleted=False)
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated, IsCommunityMember]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Filter messages by community if specified"""
        queryset = self.queryset
        community_id = self.request.query_params.get('community')
        
        if community_id:
            queryset = queryset.filter(community_id=community_id)
        
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Send a new chat message"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save(
                sender=request.user,
                status='sent'
            )
            return Response(
                ChatMessageDetailSerializer(
                    message,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Edit a message (owner only)"""
        instance = self.get_object()
        
        if instance.sender != request.user:
            return Response(
                {'detail': 'You can only edit your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_message = request.data.get('message')
        if new_message:
            instance.edit_message(new_message)
        
        return Response(
            ChatMessageSerializer(instance, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a message (owner only)"""
        instance = self.get_object()
        
        if instance.sender != request.user:
            return Response(
                {'detail': 'You can only delete your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        message.mark_as_read()
        
        ChatMessageReadReceipt.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        return Response(
            {'detail': 'Message marked as read.'},
            status=status.HTTP_200_OK
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading notifications.
    
    Endpoints:
    - GET /api/notifications/ - List user's notifications
    - GET /api/notifications/{id}/ - Get notification details
    - POST /api/notifications/{id}/mark-as-read/ - Mark as read
    - POST /api/notifications/mark-all-as-read/ - Mark all as read
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """Only return notifications for current user"""
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response(
            {'detail': 'Notification marked as read.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read for user"""
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response(
            {'detail': f'{unread_count} notifications marked as read.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})
