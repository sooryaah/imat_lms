from django.urls import path
from .views import ChatAPIView, FAQListView

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat-api'),
    path('faqs/', FAQListView.as_view(), name='faq-list'),
]
