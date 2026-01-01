"""
WebSocket URL routing for Django Channels.

Maps WebSocket connections to appropriate consumers.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/community/chat/(?P<community_id>\w+)/$',
        consumers.ChatConsumer.as_asgi(),
        name='chat_consumer'
    ),
    re_path(
        r'ws/notifications/$',
        consumers.NotificationConsumer.as_asgi(),
        name='notification_consumer'
    ),
]
