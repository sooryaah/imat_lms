from rest_framework import serializers
from .models import (Assignment, AssignmentSubmission, AssignmentSubmissionFile, 
                     AssignmentGradeRubric, AssignmentSubmissionRubricScore)
from django.contrib.auth import get_user_model

User = get_user_model()


class AssignmentSubmissionFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded files in submissions"""
    file_size_mb = serializers.ReadOnlyField()

    class Meta:
        model = AssignmentSubmissionFile
        fields = ['id', 'original_filename', 'file_type', 'file_size', 'file_size_mb', 'uploaded_at', 'file']
        read_only_fields = ['id', 'file_type', 'file_size', 'file_size_mb', 'uploaded_at']


class AssignmentGradeRubricSerializer(serializers.ModelSerializer):
    """Serializer for grading rubric criteria"""

    class Meta:
        model = AssignmentGradeRubric
        fields = ['id', 'criteria', 'max_points', 'description', 'order']


class AssignmentSubmissionRubricScoreSerializer(serializers.ModelSerializer):
    """Serializer for rubric scores in submissions"""
    criterion_name = serializers.CharField(source='criterion.criteria', read_only=True)
    criterion_max_points = serializers.IntegerField(source='criterion.max_points', read_only=True)

    class Meta:
        model = AssignmentSubmissionRubricScore
        fields = ['id', 'criterion', 'criterion_name', 'criterion_max_points', 'points_awarded', 'notes']


class AssignmentSubmissionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for submission with all related data"""
    student_email = serializers.EmailField(source='student.email', read_only=True)
    graded_by_email = serializers.EmailField(source='graded_by.email', read_only=True, allow_null=True)
    files = AssignmentSubmissionFileSerializer(many=True, read_only=True)
    rubric_scores = AssignmentSubmissionRubricScoreSerializer(many=True, read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'student_email', 'submission_text', 
                  'submission_date', 'is_late', 'status', 'is_graded', 'grade', 
                  'points_earned', 'feedback', 'graded_by', 'graded_by_email', 
                  'graded_at', 'created_at', 'updated_at', 'files', 'rubric_scores']
        read_only_fields = ['id', 'submission_date', 'is_late', 'created_at', 'updated_at', 'student']


class AssignmentSubmissionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for submission lists"""
    student_email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'student_email', 'submission_date', 
                  'is_late', 'status', 'grade', 'points_earned']
        read_only_fields = ['id', 'submission_date', 'is_late']


class AssignmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for assignment with all related data"""
    course_title = serializers.CharField(source='course.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    graded_count = serializers.SerializerMethodField()
    rubric_criteria = AssignmentGradeRubricSerializer(many=True, read_only=True, source='rubric_criteria')
    submissions = AssignmentSubmissionListSerializer(many=True, read_only=True)
    student_submission = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ['id', 'course', 'course_title', 'module', 'title', 'description', 
                  'instructions', 'due_date', 'points', 'allow_late_submission', 
                  'late_submission_penalty', 'is_published', 'allow_file_upload', 
                  'max_file_size', 'allowed_file_types', 'created_by', 'created_by_email',
                  'created_at', 'updated_at', 'is_overdue', 'days_until_due', 
                  'submission_count', 'graded_count', 'rubric_criteria', 'submissions',
                  'student_submission']
        read_only_fields = ['id', 'created_by', 'created_by_email', 'created_at', 'updated_at']

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def get_days_until_due(self, obj):
        return obj.days_until_due()

    def get_submission_count(self, obj):
        return obj.submission_count()

    def get_graded_count(self, obj):
        return obj.graded_count()

    def get_student_submission(self, obj):
        """If request is from a student, include their submission"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'role'):
            try:
                submission = obj.submissions.get(student=request.user)
                return AssignmentSubmissionDetailSerializer(submission).data
            except AssignmentSubmission.DoesNotExist:
                return None
        return None


class AssignmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for assignment lists"""
    course_title = serializers.CharField(source='course.name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_until_due = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    graded_count = serializers.SerializerMethodField()
    student_submission = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ['id', 'course', 'course_title', 'title', 'due_date', 'points',
                  'is_published', 'created_at', 'is_overdue', 'days_until_due',
                  'submission_count', 'graded_count', 'student_submission']
        read_only_fields = fields

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def get_days_until_due(self, obj):
        return obj.days_until_due()

    def get_submission_count(self, obj):
        return obj.submission_count()

    def get_graded_count(self, obj):
        return obj.graded_count()

    def get_student_submission(self, obj):
        """If request is from a student, include their submission"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'role'):
            try:
                submission = obj.submissions.get(student=request.user)
                return AssignmentSubmissionDetailSerializer(submission).data
            except AssignmentSubmission.DoesNotExist:
                return None
        return None


class AssignmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating assignments"""

    class Meta:
        model = Assignment
        fields = ['course', 'module', 'title', 'description', 'instructions', 
                  'due_date', 'points', 'allow_late_submission', 'late_submission_penalty',
                  'is_published', 'allow_file_upload', 'max_file_size', 'allowed_file_types']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AssignmentSubmitSerializer(serializers.Serializer):
    """Serializer for student submission"""
    submission_text = serializers.CharField()
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )


class SubmissionGradeSerializer(serializers.Serializer):
    """Serializer for grading submissions"""
    grade = serializers.IntegerField(min_value=0, max_value=100, required=False, allow_null=True)
    feedback = serializers.CharField(required=False, allow_blank=True)
    rubric_scores = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )


class SubmissionReturnSerializer(serializers.Serializer):
    """Serializer for returning submission for revision"""
    feedback = serializers.CharField()
