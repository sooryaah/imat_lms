from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


class Assignment(models.Model):
    """
    Assignment model for course assignments.
    
    Attributes:
        course: ForeignKey to Course
        module: ForeignKey to Module (optional)
        title: Assignment title
        description: Brief description
        instructions: Detailed instructions
        due_date: Assignment deadline
        points: Total points possible
        allow_late_submission: Whether late submissions are allowed
        late_submission_penalty: Percentage penalty (0-100) for late work
        is_published: Whether assignment is visible to students
        allow_file_upload: Whether students can upload files
        max_file_size: Maximum file size in MB
        allowed_file_types: Comma-separated list of allowed file extensions
        created_by: User who created the assignment
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    module = models.CharField(max_length=255, null=True, blank=True, help_text="Module or unit name")
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructions = models.TextField()
    due_date = models.DateTimeField()
    points = models.IntegerField(default=100, help_text="Total points possible")
    allow_late_submission = models.BooleanField(default=True)
    late_submission_penalty = models.IntegerField(default=0, help_text="Percentage penalty (0-100)")
    is_published = models.BooleanField(default=False)
    allow_file_upload = models.BooleanField(default=True)
    max_file_size = models.IntegerField(default=20, help_text="Maximum file size in MB")
    allowed_file_types = models.CharField(max_length=500, default="pdf,doc,docx,txt", 
                                          help_text="Comma-separated file extensions")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'due_date']),
            models.Index(fields=['is_published']),
        ]

    def __str__(self):
        return f"{self.title} - {self.course.name}"

    def is_overdue(self):
        """Check if assignment is past due date"""
        return timezone.now() > self.due_date

    def days_until_due(self):
        """Days remaining until due date (negative if overdue)"""
        delta = self.due_date - timezone.now()
        return delta.days

    def submission_count(self):
        """Total number of submissions"""
        return self.submissions.count()

    def graded_count(self):
        """Number of graded submissions"""
        return self.submissions.filter(is_graded=True).count()


class AssignmentSubmission(models.Model):
    """
    Student submission for an assignment.
    
    Attributes:
        assignment: ForeignKey to Assignment
        student: ForeignKey to User (student)
        submission_text: Student's written response
        submission_date: When submission was made
        is_late: Whether submission is after due date
        status: Current status (submitted/grading/graded/returned)
        is_graded: Whether submission has been graded
        grade: Grade given (0-100)
        points_earned: Points awarded
        feedback: Instructor feedback
        graded_by: User who graded it
        graded_at: When it was graded
        created_at: Timestamp of submission
        updated_at: Timestamp of last update
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('grading', 'Grading'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    submission_text = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    is_graded = models.BooleanField(default=False)
    grade = models.IntegerField(null=True, blank=True, help_text="Grade 0-100")
    points_earned = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submission_date']
        indexes = [
            models.Index(fields=['assignment', 'is_graded']),
            models.Index(fields=['student', 'is_graded']),
        ]

    def __str__(self):
        return f"{self.student.email} - {self.assignment.title}"

    def save(self, *args, **kwargs):
        """Check if submission is late"""
        if not self.pk:  # Only check on creation
            self.is_late = self.submission_date > self.assignment.due_date
        super().save(*args, **kwargs)


class AssignmentSubmissionFile(models.Model):
    """
    File uploaded with a submission.
    
    Attributes:
        submission: ForeignKey to AssignmentSubmission
        file: The uploaded file
        original_filename: Original name of the file
        file_type: File extension (pdf, doc, etc.)
        file_size: Size in bytes
        uploaded_at: Timestamp of upload
    """
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='assignments/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # pdf, doc, docx, txt, etc.
    file_size = models.IntegerField()  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_filename

    @property
    def file_size_mb(self):
        """Return file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)


class AssignmentGradeRubric(models.Model):
    """
    Grading rubric criteria for an assignment.
    
    Attributes:
        assignment: ForeignKey to Assignment
        criteria: Name of grading criterion
        max_points: Maximum points for this criterion
        description: Detailed description of criterion
        order: Order in which to display criteria
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='rubric_criteria')
    criteria = models.CharField(max_length=255)
    max_points = models.IntegerField()
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('assignment', 'criteria')
        ordering = ['order']

    def __str__(self):
        return f"{self.assignment.title} - {self.criteria}"


class AssignmentSubmissionRubricScore(models.Model):
    """
    Score given for a specific rubric criterion on a submission.
    
    Attributes:
        submission: ForeignKey to AssignmentSubmission
        criterion: ForeignKey to AssignmentGradeRubric
        points_awarded: Points given for this criterion
        notes: Detailed notes on this score
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='rubric_scores')
    criterion = models.ForeignKey(AssignmentGradeRubric, on_delete=models.CASCADE)
    points_awarded = models.IntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('submission', 'criterion')
        ordering = ['criterion__order']

    def __str__(self):
        return f"{self.submission} - {self.criterion.criteria}: {self.points_awarded} pts"
