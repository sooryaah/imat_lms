from rest_framework import serializers
from .models import AttendanceSession, AttendanceRecord


class AttendanceSessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    linked_content_title = serializers.CharField(source='linked_content.title', read_only=True)

    class Meta:
        model = AttendanceSession
        fields = ['id', 'course', 'course_title', 'session_date', 'session_type', 'is_required',
                  'linked_content', 'linked_content_title', 'title', 'notes', 'created_at']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    session_date = serializers.DateField(source='session.session_date', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    course = serializers.CharField(source='session.course.title', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'session', 'session_date', 'session_title', 'course', 'user', 'status', 'logged_at']
        read_only_fields = ['user', 'logged_at']


class AttendanceSummarySerializer(serializers.Serializer):
    total_present = serializers.IntegerField()
    total_absent = serializers.IntegerField()
    total_excused = serializers.IntegerField()
    total_classes = serializers.IntegerField()