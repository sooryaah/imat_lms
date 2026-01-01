from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import AttendanceSession, AttendanceRecord
from .serializers import (
    AttendanceSessionSerializer,
    AttendanceRecordSerializer,
    AttendanceSummarySerializer,
)
from courses.permissions import IsAdminOrReadOnly, IsAdminUser
from courses.models import Enrollment


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class AttendanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return AttendanceRecord.objects.select_related('session', 'session__course').all()
        return AttendanceRecord.objects.select_related('session', 'session__course').filter(user=user)

    @action(detail=False, methods=['get'])
    def my_summary(self, request):
        user = request.user
        total_present = AttendanceRecord.objects.filter(user=user, status='present').count()
        total_absent = AttendanceRecord.objects.filter(user=user, status='absent').count()
        total_excused = AttendanceRecord.objects.filter(user=user, status='excused').count()
        total_classes = AttendanceSession.objects.filter(
            course__in=Enrollment.objects.filter(user=user, is_active=True).values('course')
        ).count()
        payload = {
            'total_present': total_present,
            'total_absent': total_absent,
            'total_excused': total_excused,
            'total_classes': total_classes,
        }
        return Response(payload)

    @action(detail=False, methods=['get'])
    def my_course(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'error': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        # verify enrollment
        enrollment = get_object_or_404(Enrollment, user=request.user, course_id=course_id, is_active=True)
        # sessions
        sessions = AttendanceSession.objects.filter(course_id=course_id).order_by('session_date')
        records = AttendanceRecord.objects.filter(user=request.user, session__in=sessions)
        by_session = {r.session_id: r for r in records}
        data = []
        for s in sessions:
            rec = by_session.get(s.id)
            data.append({
                'session_id': s.id,
                'date': s.session_date,
                'title': s.title,
                'type': s.session_type,
                'is_required': s.is_required,
                'status': rec.status if rec else 'scheduled'
            })
        return Response({'course_id': course_id, 'sessions': data})


class AdminAttendanceActionsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def mark_present(self, request):
        session_id = request.data.get('session_id')
        user_ids = request.data.get('user_ids', [])
        if not session_id or not isinstance(user_ids, list):
            return Response({'error': 'session_id and user_ids list are required'}, status=status.HTTP_400_BAD_REQUEST)
        session = get_object_or_404(AttendanceSession, id=session_id)
        # mark present for given users
        for uid in user_ids:
            AttendanceRecord.objects.update_or_create(
                session=session,
                user_id=uid,
                defaults={'status': 'present'}
            )
        return Response({'message': 'Attendance marked present for specified users'})

    @action(detail=False, methods=['post'])
    def mark_absent_for_others(self, request):
        session_id = request.data.get('session_id')
        present_user_ids = request.data.get('present_user_ids', [])
        if not session_id:
            return Response({'error': 'session_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        session = get_object_or_404(AttendanceSession, id=session_id)
        # find enrolled users for this course
        enrolled_user_ids = list(Enrollment.objects.filter(course=session.course, is_active=True).values_list('user_id', flat=True))
        # mark absent for those not present
        for uid in enrolled_user_ids:
            if uid in present_user_ids:
                continue
            AttendanceRecord.objects.update_or_create(
                session=session,
                user_id=uid,
                defaults={'status': 'absent'}
            )
        return Response({'message': 'Absent marked for non-present users'})