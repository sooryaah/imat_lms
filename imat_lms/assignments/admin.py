from django.contrib import admin
from .models import (Assignment, AssignmentSubmission, AssignmentSubmissionFile, 
                     AssignmentGradeRubric, AssignmentSubmissionRubricScore)


class AssignmentGradeRubricInline(admin.TabularInline):
    """Inline admin for rubric criteria"""
    model = AssignmentGradeRubric
    extra = 1
    fields = ['criteria', 'max_points', 'description', 'order']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin interface for assignments"""
    list_display = ['title', 'course', 'due_date', 'points', 'is_published', 'submission_count', 'graded_count', 'created_at']
    list_filter = ['is_published', 'course', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [AssignmentGradeRubricInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'module', 'title', 'description', 'instructions')
        }),
        ('Due Date & Points', {
            'fields': ('due_date', 'points')
        }),
        ('Late Submission Settings', {
            'fields': ('allow_late_submission', 'late_submission_penalty'),
            'classes': ('collapse',)
        }),
        ('File Upload Settings', {
            'fields': ('allow_file_upload', 'max_file_size', 'allowed_file_types'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_published',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class AssignmentSubmissionFileInline(admin.TabularInline):
    """Inline admin for submission files"""
    model = AssignmentSubmissionFile
    extra = 0
    readonly_fields = ['original_filename', 'file_type', 'file_size', 'uploaded_at', 'file']
    can_delete = True


class AssignmentSubmissionRubricScoreInline(admin.TabularInline):
    """Inline admin for rubric scores"""
    model = AssignmentSubmissionRubricScore
    extra = 0
    fields = ['criterion', 'points_awarded', 'notes']


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    """Admin interface for submissions"""
    list_display = ['student', 'assignment', 'submission_date', 'is_late', 'status', 'grade', 'points_earned', 'is_graded']
    list_filter = ['status', 'is_graded', 'is_late', 'submission_date', 'assignment__course']
    search_fields = ['student__email', 'assignment__title', 'student__first_name', 'student__last_name']
    readonly_fields = ['submission_date', 'created_at', 'updated_at', 'is_late', 'student']
    inlines = [AssignmentSubmissionFileInline, AssignmentSubmissionRubricScoreInline]
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('assignment', 'student', 'submission_text', 'submission_date')
        }),
        ('Late Submission', {
            'fields': ('is_late',)
        }),
        ('Grading', {
            'fields': ('status', 'is_graded', 'grade', 'points_earned', 'feedback', 'graded_by', 'graded_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual submission creation in admin"""
        return False


@admin.register(AssignmentSubmissionFile)
class AssignmentSubmissionFileAdmin(admin.ModelAdmin):
    """Admin interface for submission files"""
    list_display = ['original_filename', 'submission', 'file_type', 'file_size_mb', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['original_filename', 'submission__student__email']
    readonly_fields = ['file_type', 'file_size', 'uploaded_at', 'original_filename']
    
    fieldsets = (
        ('File Info', {
            'fields': ('submission', 'original_filename', 'file_type', 'file_size', 'file')
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        return f"{obj.file_size_mb} MB"
    file_size_mb.short_description = "File Size"


@admin.register(AssignmentGradeRubric)
class AssignmentGradeRubricAdmin(admin.ModelAdmin):
    """Admin interface for rubric criteria"""
    list_display = ['criteria', 'assignment', 'max_points', 'order']
    list_filter = ['assignment__course', 'assignment']
    search_fields = ['criteria', 'assignment__title']
    ordering = ['assignment', 'order']


@admin.register(AssignmentSubmissionRubricScore)
class AssignmentSubmissionRubricScoreAdmin(admin.ModelAdmin):
    """Admin interface for rubric scores"""
    list_display = ['submission', 'criterion', 'points_awarded', 'created_at']
    list_filter = ['criterion__assignment', 'created_at']
    search_fields = ['submission__student__email', 'criterion__criteria']
    readonly_fields = ['created_at', 'updated_at']
