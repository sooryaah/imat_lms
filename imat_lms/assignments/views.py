from rest_framework import viewsets, status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import (Assignment, AssignmentSubmission, AssignmentSubmissionFile, 
                     AssignmentGradeRubric, AssignmentSubmissionRubricScore)
from .serializers import (AssignmentDetailSerializer, AssignmentListSerializer, 
                          AssignmentCreateUpdateSerializer, AssignmentGradeRubricSerializer,
                          AssignmentSubmitSerializer, AssignmentSubmissionDetailSerializer,
                          AssignmentSubmissionListSerializer, SubmissionGradeSerializer,
                          SubmissionReturnSerializer, AssignmentSubmissionFileSerializer)
from .permissions import (CanCreateAssignment, CanEditAssignment, CanViewAssignment,
                          CanViewSubmission, CanGradeSubmission, CanSubmitAssignment,
                          CanEditSubmission, IsStudent, IsInstructor, IsAdmin)
from courses.models import Enrollment


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing assignments.
    
    Actions:
        list: Get all assignments (filtered by role)
        create: Create new assignment (instructor/admin only)
        retrieve: Get assignment details
        update: Update assignment (instructor/admin only)
        partial_update: Partial update assignment
        destroy: Delete assignment
        submit: Submit assignment as student
        submissions: View submissions for an assignment
        rubric: Create or list rubric criteria
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter assignments based on user role"""
        user = self.request.user
        
        if not hasattr(user, 'role'):
            return Assignment.objects.none()
        
        # Admins see all assignments
        if user.role == 'admin':
            return Assignment.objects.all()
        
        # Instructors see their own assignments
        if user.role == 'instructor':
            return Assignment.objects.filter(created_by=user)
        
        # Students see only published assignments for their courses
        if user.role == 'student':
            enrolled_courses = Enrollment.objects.filter(
                student=user,
                status='active'
            ).values_list('course_id', flat=True)
            return Assignment.objects.filter(
                course_id__in=enrolled_courses,
                is_published=True
            )
        
        return Assignment.objects.none()

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return AssignmentCreateUpdateSerializer
        elif self.action == 'retrieve':
            return AssignmentDetailSerializer
        else:
            return AssignmentListSerializer

    def create(self, request, *args, **kwargs):
        """Create new assignment (instructor/admin only)"""
        if not (hasattr(request.user, 'role') and request.user.role in ['admin', 'instructor']):
            return Response(
                {'detail': 'Only instructors and admins can create assignments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update assignment"""
        assignment = self.get_object()
        if not (request.user.role == 'admin' or assignment.created_by == request.user):
            return Response(
                {'detail': 'You do not have permission to edit this assignment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete assignment"""
        assignment = self.get_object()
        if not (request.user.role == 'admin' or assignment.created_by == request.user):
            return Response(
                {'detail': 'You do not have permission to delete this assignment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSubmitAssignment])
    def submit(self, request, pk=None):
        """
        Submit assignment as student.
        
        Request (multipart/form-data):
            submission_text: Student's written response
            files: (optional) List of files to upload
        """
        assignment = self.get_object()
        
        # Check if student is enrolled
        if not Enrollment.objects.filter(
            student=request.user,
            course=assignment.course,
            status='active'
        ).exists():
            return Response(
                {'detail': 'You are not enrolled in this course.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if assignment is published
        if not assignment.is_published:
            return Response(
                {'detail': 'This assignment is not yet published.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create submission
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=request.user,
            defaults={'submission_text': ''}
        )
        
        # Update submission text
        submission.submission_text = request.data.get('submission_text', '')
        submission.status = 'submitted'
        submission.save()
        
        # Handle file uploads
        files = request.FILES.getlist('files', [])
        if files:
            for file in files:
                # Check file size
                if file.size > assignment.max_file_size * 1024 * 1024:
                    return Response(
                        {'detail': f'File {file.name} exceeds maximum size of {assignment.max_file_size}MB.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check file type
                file_ext = file.name.split('.')[-1].lower()
                allowed_types = [t.strip() for t in assignment.allowed_file_types.split(',')]
                if file_ext not in allowed_types:
                    return Response(
                        {'detail': f'File type .{file_ext} is not allowed. Allowed: {assignment.allowed_file_types}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Save file
                AssignmentSubmissionFile.objects.create(
                    submission=submission,
                    file=file,
                    original_filename=file.name,
                    file_type=file_ext,
                    file_size=file.size
                )
        
        serializer = AssignmentSubmissionDetailSerializer(submission)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """
        Get all submissions for an assignment.
        Only accessible to instructors and admins for their courses.
        
        Query Parameters:
            status: Filter by submission status (submitted/grading/graded/returned)
        """
        assignment = self.get_object()
        
        # Check permission
        if not (request.user.role == 'admin' or assignment.created_by == request.user):
            return Response(
                {'detail': 'You do not have permission to view submissions for this assignment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submissions = assignment.submissions.all()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        
        serializer = AssignmentSubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rubric(self, request, pk=None):
        """
        Create rubric criteria for assignment (POST).
        List rubric criteria (GET).
        """
        assignment = self.get_object()
        
        # Check permission - only instructor who created it or admin
        if not (request.user.role == 'admin' or assignment.created_by == request.user):
            return Response(
                {'detail': 'You do not have permission to manage rubrics for this assignment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'POST':
            serializer = AssignmentGradeRubricSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(assignment=assignment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentSubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing assignment submissions.
    
    Actions:
        list: Get submissions (filtered by role)
        retrieve: Get submission details
        update: Update submission (student only, before grading)
        partial_update: Partial update submission
        grade: Grade a submission (instructor/admin only)
        return_for_revision: Return submission for revision
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter submissions based on user role"""
        user = self.request.user
        
        if not hasattr(user, 'role'):
            return AssignmentSubmission.objects.none()
        
        # Admins see all submissions
        if user.role == 'admin':
            return AssignmentSubmission.objects.all()
        
        # Instructors see submissions from their courses
        if user.role == 'instructor':
            return AssignmentSubmission.objects.filter(
                assignment__created_by=user
            ) | AssignmentSubmission.objects.filter(
                assignment__course__instructor=user
            )
        
        # Students see only their own submissions
        if user.role == 'student':
            return AssignmentSubmission.objects.filter(student=user)
        
        return AssignmentSubmission.objects.none()

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action in ['retrieve']:
            return AssignmentSubmissionDetailSerializer
        elif self.action in ['grade', 'return_for_revision']:
            return SubmissionGradeSerializer
        else:
            return AssignmentSubmissionListSerializer

    def update(self, request, *args, **kwargs):
        """Update submission (students only, before grading)"""
        submission = self.get_object()
        
        if submission.student != request.user:
            return Response(
                {'detail': 'You can only edit your own submissions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if submission.is_graded:
            return Response(
                {'detail': 'Cannot edit a submission that has been graded.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """
        Grade a submission.
        
        Request:
            grade: Grade 0-100
            feedback: Text feedback
            rubric_scores: Array of {criterion: id, points_awarded: int}
        """
        submission = self.get_object()
        
        # Check permission
        if not (request.user.role == 'admin' or submission.assignment.created_by == request.user):
            return Response(
                {'detail': 'You do not have permission to grade this submission.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SubmissionGradeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Update grade and feedback
        if 'grade' in serializer.validated_data and serializer.validated_data['grade'] is not None:
            submission.grade = serializer.validated_data['grade']
            submission.is_graded = True
            submission.status = 'graded'
            
            # Calculate points earned with late penalty
            points = int(submission.grade / 100 * submission.assignment.points)
            
            if submission.is_late and submission.assignment.late_submission_penalty > 0:
                penalty = int(points * submission.assignment.late_submission_penalty / 100)
                points = max(0, points - penalty)
            
            submission.points_earned = points
        
        if 'feedback' in serializer.validated_data:
            submission.feedback = serializer.validated_data['feedback']
        
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        # Handle rubric scores
        if 'rubric_scores' in serializer.validated_data and serializer.validated_data['rubric_scores']:
            for score_data in serializer.validated_data['rubric_scores']:
                criterion_id = score_data.get('criterion')
                points_awarded = score_data.get('points_awarded')
                notes = score_data.get('notes', '')
                
                if criterion_id and points_awarded is not None:
                    AssignmentSubmissionRubricScore.objects.update_or_create(
                        submission=submission,
                        criterion_id=criterion_id,
                        defaults={'points_awarded': points_awarded, 'notes': notes}
                    )
        
        return Response(
            AssignmentSubmissionDetailSerializer(submission).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def return_for_revision(self, request, pk=None):
        """
        Return submission for revision.
        
        Request:
            feedback: Feedback for the revision
        """
        submission = self.get_object()
        
        # Check permission
        if not (request.user.role == 'admin' or submission.assignment.created_by == request.user):
            return Response(
                {'detail': 'You do not have permission to return this submission.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SubmissionReturnSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        submission.status = 'returned'
        submission.feedback = serializer.validated_data['feedback']
        submission.is_graded = False
        submission.save()
        
        return Response(
            AssignmentSubmissionDetailSerializer(submission).data,
            status=status.HTTP_200_OK
        )


class AssignmentRubricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing rubric criteria.
    """
    serializer_class = AssignmentGradeRubricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get rubric criteria, optionally filtered by assignment"""
        queryset = AssignmentGradeRubric.objects.all()
        
        assignment_id = self.request.query_params.get('assignment_id')
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)
        
        return queryset
