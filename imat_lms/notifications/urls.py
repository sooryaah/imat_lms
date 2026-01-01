from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, NotificationPreferenceViewSet,
    NotificationTypeViewSet, NotificationTemplateViewSet
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'types', NotificationTypeViewSet, basename='notification-type')
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')

urlpatterns = [
    path('', include(router.urls)),
]
