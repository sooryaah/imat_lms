from rest_framework import serializers
from .models import (
    Course, Module, Content, Quiz, Question, QuestionOption,
    Enrollment, Progress, QuizAttempt, QuizAnswer, Review, Application
)
from django.utils import timezone


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'is_correct', 'order']
        extra_kwargs = {
            'is_correct': {'write_only': True}  # Don't expose correct answer to students
        }


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'points', 'order', 'explanation', 'options']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    total_questions = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'passing_score', 'time_limit', 'max_attempts', 
                  'total_questions', 'total_points', 'questions']

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(q.points for q in obj.questions.all())


class ContentSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)
    is_accessible = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = ['id', 'title', 'description', 'content_type', 'order', 
                  'video_url', 'video_duration', 'text_content', 
                  'is_preview', 'quiz', 'is_accessible']

    def get_is_accessible(self, obj):
        """Check if content is accessible to the current user"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_preview
        
        # Admin can access all
        if request.user.is_admin:
            return True
        
        # Check enrollment
        enrolled = Enrollment.objects.filter(
            user=request.user,
            course=obj.module.course,
            is_active=True
        ).exists()
        
        return enrolled or obj.is_preview


class ModuleSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(many=True, read_only=True)
    content_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'content_count', 'contents']

    def get_content_count(self, obj):
        return obj.contents.count()


class CourseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for course listing"""
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'eligibility', 'price', 'thumbnail', 
                  'duration_months', 'total_lessons', 'total_modules', 
                  'rating', 'is_trending', 'category', 'level', 'course_type', 'is_enrolled']

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(
            user=request.user, 
            course=obj, 
            is_active=True
        ).exists()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single course view"""
    modules = ModuleSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    enrollment_info = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'eligibility', 'price', 'thumbnail', 
                  'duration_months', 'total_lessons', 'total_modules', 
                  'rating', 'is_trending', 'category', 'level', 'course_type',
                  'created_at', 'modules', 'is_enrolled', 'enrollment_info',
                  'reviews_count', 'average_rating']

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Enrollment.objects.filter(
            user=request.user, 
            course=obj, 
            is_active=True
        ).exists()

    def get_enrollment_info(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        enrollment = Enrollment.objects.filter(
            user=request.user, 
            course=obj, 
            is_active=True
        ).first()
        
        if enrollment:
            return {
                'enrollment_date': enrollment.enrollment_date,
                'progress_percentage': enrollment.progress_percentage,
                'expiry_date': enrollment.expiry_date,
            }
        return None

    def get_reviews_count(self, obj):
        return obj.enrollments.filter(review__isnull=False).count()

    def get_average_rating(self, obj):
        reviews = Review.objects.filter(enrollment__course=obj)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'enrollment_date', 'is_active', 
                  'expiry_date', 'completed_at', 'progress_percentage']


class ProgressSerializer(serializers.ModelSerializer):
    content_title = serializers.CharField(source='content.title', read_only=True)
    content_type = serializers.CharField(source='content.content_type', read_only=True)

    class Meta:
        model = Progress
        fields = ['id', 'content', 'content_title', 'content_type', 
                  'is_completed', 'completion_date', 'time_spent', 
                  'last_position', 'updated_at']


class ProgressUpdateSerializer(serializers.Serializer):
    """Serializer for updating progress"""
    content_id = serializers.IntegerField()
    is_completed = serializers.BooleanField(required=False)
    time_spent = serializers.IntegerField(required=False)
    last_position = serializers.IntegerField(required=False)

    def validate_content_id(self, value):
        if not Content.objects.filter(id=value).exists():
            raise serializers.ValidationError("Content does not exist")
        return value


class QuizAnswerSubmitSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers"""
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField(required=False, allow_null=True)
    text_answer = serializers.CharField(required=False, allow_blank=True)


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.content.title', read_only=True)
    answers = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'quiz_title', 'score', 'passed', 
                  'attempt_number', 'started_at', 'completed_at', 'answers']

    def get_answers(self, obj):
        if obj.completed_at:
            answers = obj.answers.all()
            return [{
                'question_id': ans.question.id,
                'question_text': ans.question.question_text,
                'selected_option_id': ans.selected_option.id if ans.selected_option else None,
                'is_correct': ans.is_correct,
                'points_earned': ans.points_earned,
                'explanation': ans.question.explanation
            } for ans in answers]
        return []


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='enrollment.user.full_name', read_only=True)
    user_email = serializers.CharField(source='enrollment.user.email', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'created_at', 'updated_at',
                  'user_name', 'user_email', 'course_title']
        read_only_fields = ['created_at', 'updated_at']


class ApplicationSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'course', 'course_title', 'user', 'user_email',
            'full_name', 'phone', 'email', 'location', 'qualification', 'notes',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to create/update courses"""
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'eligibility', 'price', 'thumbnail', 
                  'is_published', 'duration_months', 'category', 'level', 
                  'is_trending', 'course_type']
        
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to create/update modules"""
    
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'description', 'order']


class ContentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to create/update content"""
    
    class Meta:
        model = Content
        fields = ['id', 'module', 'title', 'description', 'content_type', 
                  'order', 'video_url', 'video_duration', 'file_upload', 
                  'text_content', 'is_preview']


class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to create/update quizzes"""
    
    class Meta:
        model = Quiz
        fields = ['id', 'content', 'passing_score', 'time_limit', 'max_attempts']


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to create/update questions"""
    options = QuestionOptionSerializer(many=True, required=False)
    
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'question_text', 'question_type', 
                  'points', 'order', 'explanation', 'options']
    
    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        question = Question.objects.create(**validated_data)
        
        for option_data in options_data:
            QuestionOption.objects.create(question=question, **option_data)
        
        return question
    
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        
        # Update question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update options if provided
        if options_data is not None:
            # Delete existing options
            instance.options.all().delete()
            # Create new options
            for option_data in options_data:
                QuestionOption.objects.create(question=instance, **option_data)
        
        return instance
 