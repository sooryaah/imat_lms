from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('language', 'Language Course'),
        ('media', 'Media Course'),
        ('professional', 'Professional Course'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    eligibility = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    is_published = models.BooleanField(default=False)
    course_type = models.CharField(
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='professional'
    )
    category = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], default='beginner')
    duration_months = models.IntegerField(default=6)
    total_lessons = models.IntegerField(default=0)
    total_modules = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_courses')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

    def update_counts(self):
        """Update total modules and lessons count"""
        self.total_modules = self.modules.count()
        self.total_lessons = Content.objects.filter(module__course=self).count()
        self.save(update_fields=['total_modules', 'total_lessons'])



class Module(models.Model):
    """Organizes content within a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Content(models.Model):
    """Stores the actual learning material (video/quiz/document)"""
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('quiz', 'Quiz'),
        ('document', 'Document'),
        ('text', 'Text'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    
    # Video/Document fields
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for hosted video (Vimeo, YouTube, S3, etc.)")
    video_duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    file_upload = models.FileField(upload_to='course_materials/', null=True, blank=True)
    
    # Text content
    text_content = models.TextField(blank=True)
    
    # Meta
    is_preview = models.BooleanField(default=False, help_text="Can be accessed without enrollment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ['module', 'order']
        verbose_name_plural = 'Contents'

    def __str__(self):
        return f"{self.module.course.title} - {self.module.title} - {self.title}"


class Quiz(models.Model):
    """Quiz associated with content"""
    content = models.OneToOneField(Content, on_delete=models.CASCADE, related_name='quiz')
    passing_score = models.IntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    max_attempts = models.IntegerField(default=3, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quiz for {self.content.title}"


class Question(models.Model):
    """Individual quiz question"""
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.quiz.content.title} - Q{self.order}"


class QuestionOption(models.Model):
    """Options for multiple choice questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.option_text[:30]}"


class Enrollment(models.Model):
    """Links a user to a purchased course"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    @property
    def progress_percentage(self):
        """Calculate the progress percentage"""
        total_contents = Content.objects.filter(module__course=self.course).count()
        if total_contents == 0:
            return 0
        completed = self.progress_records.filter(is_completed=True).count()
        return round((completed / total_contents) * 100, 2)


class Progress(models.Model):
    """Tracks a student's progress through course content"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress_records')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='progress_records')
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")
    last_position = models.IntegerField(default=0, help_text="Last video position in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'content']
        verbose_name_plural = 'Progress'
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
        ]

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.content.title} - {'Completed' if self.is_completed else 'In Progress'}"


class QuizAttempt(models.Model):
    """Records quiz attempts by students"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    passed = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.quiz.content.title} - Attempt {self.attempt_number}"


class QuizAnswer(models.Model):
    """Stores student answers for quiz questions"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Answer for {self.question.question_text[:30]}"


class Review(models.Model):
    """Course reviews and ratings from enrolled students"""
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Application(models.Model):
    """Stores pre-enrollment application details prior to payment"""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('in_payment', 'In Payment'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_applications'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    location = models.CharField(max_length=255, blank=True)
    qualification = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"Application: {self.full_name} -> {self.course.title} ({self.status})"

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.enrollment.course.title} - {self.rating}★"
