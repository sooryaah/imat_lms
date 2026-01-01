"""
WebSocket consumers for real-time chat using Django Channels.

Implements:
- ChatConsumer: Real-time message delivery and read status
- PresenceConsumer: Track user presence in communities
- NotificationConsumer: Real-time notification delivery
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    
    Features:
    - Real-time message delivery
    - Message read status tracking
    - Typing indicators
    - User presence
    - Message editing and deletion
    
    WebSocket Message Format:
    {
        "type": "chat_message|typing|read_receipt|user_joined|user_left",
        "message": "...",
        "community_id": 1,
        "user_id": 1
    }
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.community_id = self.scope['url_route']['kwargs']['community_id']
        self.room_group_name = f'chat_{self.community_id}'
        self.user = self.scope['user']

        # Authenticate user
        if not self.user.is_authenticated:
            await self.close()
            return

        # Add user to group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'user_email': self.user.email,
                'timestamp': timezone.now().isoformat(),
            }
        )

        # Log connection
        logger.info(f"User {self.user.email} connected to chat_{self.community_id}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'user_email': self.user.email,
                'timestamp': timezone.now().isoformat(),
            }
        )

        # Remove from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"User {self.user.email} disconnected from chat_{self.community_id}")

    async def receive(self, text_data):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(json.dumps({'error': 'Invalid message format'}))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(json.dumps({'error': 'Server error'}))

    async def handle_chat_message(self, data):
        """Handle chat message"""
        message = data.get('message')
        message_type = data.get('message_type', 'text')
        attachment = data.get('attachment')

        if not message:
            await self.send(json.dumps({'error': 'Message cannot be empty'}))
            return

        # Save message to database
        saved_message = await self.save_chat_message(message, message_type, attachment)

        if saved_message:
            # Broadcast to all users in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message_id': saved_message['id'],
                    'message': saved_message['message'],
                    'message_type': saved_message['message_type'],
                    'sender_id': saved_message['sender_id'],
                    'sender_email': saved_message['sender_email'],
                    'created_at': saved_message['created_at'],
                }
            )

    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', True)

        # Broadcast typing indicator to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_email': self.user.email,
                'is_typing': is_typing,
                'timestamp': timezone.now().isoformat(),
            }
        )

    async def handle_read_receipt(self, data):
        """Handle message read receipt"""
        message_id = data.get('message_id')

        if not message_id:
            return

        # Save read receipt
        await self.save_read_receipt(message_id)

        # Broadcast read receipt
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt_broadcast',
                'message_id': message_id,
                'user_id': self.user.id,
                'user_email': self.user.email,
                'timestamp': timezone.now().isoformat(),
            }
        )

    # Message handlers for group_send events
    async def chat_message_broadcast(self, event):
        """Send chat message to WebSocket"""
        await self.send(json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'message_type': event['message_type'],
            'sender_id': event['sender_id'],
            'sender_email': event['sender_email'],
            'created_at': event['created_at'],
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
            'is_typing': event['is_typing'],
            'timestamp': event['timestamp'],
        }))

    async def read_receipt_broadcast(self, event):
        """Send read receipt to WebSocket"""
        await self.send(json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'user_email': event['user_email'],
            'timestamp': event['timestamp'],
        }))

    async def user_joined(self, event):
        """Send user joined notification"""
        await self.send(json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
            'timestamp': event['timestamp'],
        }))

    async def user_left(self, event):
        """Send user left notification"""
        await self.send(json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
            'timestamp': event['timestamp'],
        }))

    # Database operations
    @database_sync_to_async
    def save_chat_message(self, message, message_type, attachment):
        """Save chat message to database"""
        from .models import ChatMessage

        try:
            msg_obj = ChatMessage.objects.create(
                community_id=self.community_id,
                sender=self.user,
                message=message,
                message_type=message_type,
                status='delivered'
            )

            return {
                'id': msg_obj.id,
                'message': msg_obj.message,
                'message_type': msg_obj.message_type,
                'sender_id': msg_obj.sender.id,
                'sender_email': msg_obj.sender.email,
                'created_at': msg_obj.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")
            return None

    @database_sync_to_async
    def save_read_receipt(self, message_id):
        """Save read receipt to database"""
        from .models import ChatMessage, ChatMessageReadReceipt

        try:
            message = ChatMessage.objects.get(id=message_id)
            message.mark_as_read()

            ChatMessageReadReceipt.objects.get_or_create(
                message=message,
                user=self.user
            )
        except ChatMessage.DoesNotExist:
            logger.warning(f"Message {message_id} not found")
        except Exception as e:
            logger.error(f"Error saving read receipt: {str(e)}")


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    
    Sends notifications to users about:
    - New discussion posts
    - Replies to their posts
    - New messages
    - Mentions
    - Moderation actions
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Group name based on user
        self.room_group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        logger.info(f"User {self.user.email} connected to notifications")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"User {self.user.email} disconnected from notifications")

    async def receive(self, text_data):
        """Handle incoming messages (mainly for heartbeat)"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(json.dumps({'type': 'pong'}))

        except Exception as e:
            logger.error(f"Error in notification consumer: {str(e)}")

    # Message handlers
    async def send_notification(self, event):
        """Send notification to WebSocket"""
        await self.send(json.dumps({
            'type': 'notification',
            'notification_id': event['notification_id'],
            'notification_type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
            'actor': event.get('actor'),
            'timestamp': event['timestamp'],
        }))

    async def send_post_created(self, event):
        """Notify about new discussion post"""
        await self.send(json.dumps({
            'type': 'post_created',
            'post_id': event['post_id'],
            'post_title': event['post_title'],
            'community': event['community'],
            'author': event['author'],
            'timestamp': event['timestamp'],
        }))

    async def send_post_reply(self, event):
        """Notify about reply to post"""
        await self.send(json.dumps({
            'type': 'post_reply',
            'post_id': event['post_id'],
            'reply_id': event['reply_id'],
            'community': event['community'],
            'author': event['author'],
            'timestamp': event['timestamp'],
        }))
