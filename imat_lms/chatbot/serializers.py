from rest_framework import serializers
from .models import FAQ

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)

class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    source = serializers.CharField(default='groq')  # 'groq' or 'faq'
