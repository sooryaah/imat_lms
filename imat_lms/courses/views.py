from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404

from .models import (
    Course, Module, Content, Quiz, Question, QuestionOption,
    Enrollment, Progress, QuizAttempt, QuizAnswer, Review, Application
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    ModuleSerializer, ModuleCreateUpdateSerializer,
    ContentSerializer, ContentCreateUpdateSerializer,
    QuizSerializer, QuizCreateUpdateSerializer,
    QuestionSerializer, QuestionCreateUpdateSerializer,
    EnrollmentSerializer, ProgressSerializer, ProgressUpdateSerializer,
    QuizAttemptSerializer, QuizAnswerSubmitSerializer,
    ReviewSerializer, ApplicationSerializer
)
from .permissions import IsAdminOrReadOnly, IsEnrolledStudent, IsAdminUser


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for courses. 
    - Public users can list and view published courses
    - Students can view enrolled courses
    - Admins and instructors can create, update, delete courses
    """
    queryset = Course.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer

    def get_queryset(self):
        queryset = Course.objects.all()
        # Only show published courses to non-admin/non-instructor users
        if not self.request.user.is_authenticated or (not self.request.user.is_admin and not self.request.user.is_instructor):
            queryset = queryset.filter(is_published=True)
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        # Filter by level
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        # Filter by course_type
        course_type = self.request.query_params.get('course_type', None)
        if course_type:
            queryset = queryset.filter(course_type=course_type)
        # Filter trending
        if self.request.query_params.get('trending', None) == 'true':
            queryset = queryset.filter(is_trending=True)
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search) | Q(eligibility__icontains=search)
            )
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def modules(self, request, pk=None):
        """Get all modules for a course"""
        course = self.get_object()
        modules = course.modules.all()
        serializer = ModuleSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def progress(self, request, pk=None):
        """Get student's progress in a course"""
        course = self.get_object()
        enrollment = get_object_or_404(Enrollment, user=request.user, course=course, is_active=True)
        
        progress_data = []
        for module in course.modules.all():
            module_progress = {
                'module_id': module.id,
                'module_title': module.title,
                'contents': []
            }
            
            for content in module.contents.all():
                progress, created = Progress.objects.get_or_create(
                    enrollment=enrollment,
                    content=content
                )
                module_progress['contents'].append({
                    'content_id': content.id,
                    'content_title': content.title,
                    'content_type': content.content_type,
                    'is_completed': progress.is_completed,
                    'time_spent': progress.time_spent,
                    'last_position': progress.last_position
                })
            
            progress_data.append(module_progress)
        
        return Response({
            'course_id': course.id,
            'course_title': course.title,
            'overall_progress': enrollment.progress_percentage,
            'modules': progress_data
        })


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet for course modules - Admin only for CUD operations"""
    queryset = Module.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ModuleCreateUpdateSerializer
        return ModuleSerializer

    def perform_create(self, serializer):
        module = serializer.save()
        module.course.update_counts()

    def perform_destroy(self, instance):
        course = instance.course
        instance.delete()
        course.update_counts()


class ContentViewSet(viewsets.ModelViewSet):
    """ViewSet for course content - Admin only for CUD operations"""
    queryset = Content.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContentCreateUpdateSerializer
        return ContentSerializer

    def perform_create(self, serializer):
        content = serializer.save()
        content.module.course.update_counts()

    def perform_destroy(self, instance):
        course = instance.module.course
        instance.delete()
        course.update_counts()


class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for quizzes"""
    queryset = Quiz.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuizCreateUpdateSerializer
        return QuizSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for quiz questions - Admin only"""
    queryset = Question.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = QuestionCreateUpdateSerializer


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for enrollments.
    Students can view their own enrollments.
    Admins can view all enrollments.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Enrollment.objects.all()
        return Enrollment.objects.filter(user=user, is_active=True)

    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Get all active courses for the authenticated user"""
        enrollments = Enrollment.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('course')
        
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)


class ProgressViewSet(viewsets.ViewSet):
    """ViewSet for tracking student progress"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='update')
    def update_progress(self, request):
        """Update progress for a content item"""
        serializer = ProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        content = get_object_or_404(Content, id=serializer.validated_data['content_id'])
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course=content.module.course,
            is_active=True
        )
        
        progress, created = Progress.objects.get_or_create(
            enrollment=enrollment,
            content=content
        )
        
        # Update fields
        if 'is_completed' in serializer.validated_data:
            progress.is_completed = serializer.validated_data['is_completed']
            if progress.is_completed and not progress.completion_date:
                progress.completion_date = timezone.now()
        
        if 'time_spent' in serializer.validated_data:
            progress.time_spent = serializer.validated_data['time_spent']
        
        if 'last_position' in serializer.validated_data:
            progress.last_position = serializer.validated_data['last_position']
        
        progress.save()
        
        # Auto-mark attendance if content is linked to a required session
        try:
            from attendance.models import AttendanceSession, AttendanceRecord
            linked_sessions = AttendanceSession.objects.filter(linked_content=content, is_required=True)
            for session in linked_sessions:
                AttendanceRecord.objects.update_or_create(
                    session=session,
                    user=request.user,
                    defaults={'status': 'present'}
                )
        except Exception:
            pass

        response_serializer = ProgressSerializer(progress)
        return Response(response_serializer.data)

    @action(detail=False, methods=['get'])
    def course_progress(self, request):
        """Get progress for a specific course"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': 'course_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course_id=course_id,
            is_active=True
        )
        
        progress_records = Progress.objects.filter(enrollment=enrollment)
        serializer = ProgressSerializer(progress_records, many=True)
        
        return Response({
            'course_id': course_id,
            'overall_progress': enrollment.progress_percentage,
            'progress_records': serializer.data
        })


class QuizAttemptViewSet(viewsets.ViewSet):
    """ViewSet for quiz attempts"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new quiz attempt"""
        quiz_id = request.data.get('quiz_id')
        if not quiz_id:
            return Response(
                {'error': 'quiz_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        course = quiz.content.module.course
        
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course=course,
            is_active=True
        )
        
        # Check attempt limit
        existing_attempts = QuizAttempt.objects.filter(
            enrollment=enrollment,
            quiz=quiz
        ).count()
        
        if existing_attempts >= quiz.max_attempts:
            return Response(
                {'error': 'Maximum attempts reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            attempt_number=existing_attempts + 1,
            score=0,
            passed=False
        )
        
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit answers for a quiz attempt"""
        attempt = get_object_or_404(QuizAttempt, id=pk, enrollment__user=request.user)
        
        if attempt.completed_at:
            return Response(
                {'error': 'Quiz already submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        answers_data = request.data.get('answers', [])
        total_points = 0
        earned_points = 0
        
        for answer_data in answers_data:
            answer_serializer = QuizAnswerSubmitSerializer(data=answer_data)
            answer_serializer.is_valid(raise_exception=True)
            
            question = get_object_or_404(
                Question,
                id=answer_serializer.validated_data['question_id'],
                quiz=attempt.quiz
            )
            
            total_points += question.points
            is_correct = False
            points = 0
            
            # Check answer
            if question.question_type == 'multiple_choice':
                selected_option_id = answer_serializer.validated_data.get('selected_option_id')
                if selected_option_id:
                    selected_option = get_object_or_404(QuestionOption, id=selected_option_id)
                    is_correct = selected_option.is_correct
                    if is_correct:
                        points = question.points
                        earned_points += points
                    
                    QuizAnswer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_option=selected_option,
                        is_correct=is_correct,
                        points_earned=points
                    )
        
        # Calculate score
        if total_points > 0:
            score = (earned_points / total_points) * 100
        else:
            score = 0
        
        attempt.score = score
        attempt.passed = score >= attempt.quiz.passing_score
        attempt.completed_at = timezone.now()
        attempt.save()
        
        # Update progress if passed
        if attempt.passed:
            progress, created = Progress.objects.get_or_create(
                enrollment=attempt.enrollment,
                content=attempt.quiz.content
            )
            progress.is_completed = True
            progress.completion_date = timezone.now()
            progress.save()
        
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_attempts(self, request):
        """Get all quiz attempts for the authenticated user"""
        attempts = QuizAttempt.objects.filter(
            enrollment__user=request.user
        ).order_by('-started_at')
        
        serializer = QuizAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for course reviews"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Review.objects.all()
        
        # Filter by course if provided
        course_id = self.request.query_params.get('course_id')
        if course_id:
            return Review.objects.filter(enrollment__course_id=course_id)
        
        return Review.objects.filter(enrollment__user=user)

    def perform_create(self, serializer):
        """Create a review for an enrolled course"""
        course_id = self.request.data.get('course_id')
        enrollment = get_object_or_404(
            Enrollment,
            user=self.request.user,
            course_id=course_id,
            is_active=True
        )
        
        # Check if review already exists
        if hasattr(enrollment, 'review'):
            raise serializers.ValidationError('You have already reviewed this course')
        
        serializer.save(enrollment=enrollment)


class ApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for course applications (pre-payment form)"""
    serializer_class = ApplicationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_admin:
            return Application.objects.all()
        if user.is_authenticated:
            return Application.objects.filter(user=user)
        # Unauthenticated users cannot list; restrict to empty queryset
        return Application.objects.none()

    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        if not course or not course.is_published:
            raise serializers.ValidationError('Course not available for application')
        serializer.save(status='submitted')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start_payment(self, request, pk=None):
        """Mark application as in_payment; frontend then calls payment create_order."""
        application = self.get_object()
        if application.user and application.user != request.user and not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        application.status = 'in_payment'
        application.save(update_fields=['status'])
        return Response({'message': 'Application moved to payment'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_completed(self, request, pk=None):
        """Mark application as completed after successful payment (optional)."""
        application = self.get_object()
        if application.user and application.user != request.user and not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        application.status = 'completed'
        application.save(update_fields=['status'])
        return Response({'message': 'Application completed'}, status=status.HTTP_200_OK)
