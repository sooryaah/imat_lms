"""
URL routing for community feature endpoints.

Includes:
- Community groups
- Discussion posts
- Chat messages
- Notifications
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommunityGroupViewSet,
    DiscussionPostViewSet,
    ChatMessageViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register(r'groups', CommunityGroupViewSet, basename='community-group')
router.register(r'posts', DiscussionPostViewSet, basename='discussion-post')
router.register(r'messages', ChatMessageViewSet, basename='chat-message')
router.register(r'notifications', NotificationViewSet, basename='notification')

app_name = 'community'

urlpatterns = [
    path('', include(router.urls)),
]
