from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceSessionViewSet, AttendanceRecordViewSet, AdminAttendanceActionsViewSet

router = DefaultRouter()
router.register(r'sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'records', AttendanceRecordViewSet, basename='attendance-record')
router.register(r'admin-actions', AdminAttendanceActionsViewSet, basename='attendance-admin')

urlpatterns = [
    path('', include(router.urls)),
]