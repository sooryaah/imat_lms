from django.contrib import admin
from .models import (
    Course, Module, Content, Quiz, Question, QuestionOption,
    Enrollment, Progress, QuizAttempt, QuizAnswer, Review
)


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ['title', 'order']


class ContentInline(admin.TabularInline):
    model = Content
    extra = 1
    fields = ['title', 'content_type', 'order', 'is_preview']


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    fields = ['option_text', 'is_correct', 'order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'level', 'course_type', 'price', 'is_published', 'is_trending', 'rating', 'created_at']
    list_filter = ['is_published', 'is_trending', 'category', 'level', 'course_type', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_published', 'is_trending']
    inlines = [ModuleInline]
    readonly_fields = ['total_modules', 'total_lessons', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'thumbnail', 'category', 'level', 'course_type')
        }),
        ('Pricing & Publication', {
            'fields': ('price', 'is_published', 'is_trending')
        }),
        ('Course Details', {
            'fields': ('duration_months', 'rating', 'total_modules', 'total_lessons')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'course__title']
    inlines = [ContentInline]


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'content_type', 'order', 'is_preview']
    list_filter = ['content_type', 'is_preview', 'module__course']
    search_fields = ['title', 'module__title']
    list_editable = ['is_preview']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['content', 'passing_score', 'time_limit', 'max_attempts']
    list_filter = ['passing_score', 'time_limit']
    search_fields = ['content__title']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']
    search_fields = ['question_text']
    inlines = [QuestionOptionInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrollment_date', 'is_active', 'progress_percentage']
    list_filter = ['is_active', 'enrollment_date', 'course']
    search_fields = ['user__email', 'course__title']
    readonly_fields = ['enrollment_date', 'progress_percentage']
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = 'Progress'


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'content', 'is_completed', 'completion_date', 'time_spent']
    list_filter = ['is_completed', 'enrollment__course', 'content__content_type']
    search_fields = ['enrollment__user__email', 'content__title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'quiz', 'score', 'passed', 'attempt_number', 'started_at', 'completed_at']
    list_filter = ['passed', 'started_at', 'quiz']
    search_fields = ['enrollment__user__email', 'quiz__content__title']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_option', 'is_correct', 'points_earned']
    list_filter = ['is_correct', 'attempt__quiz']
    search_fields = ['attempt__enrollment__user__email', 'question__question_text']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'enrollment__course']
    search_fields = ['enrollment__user__email', 'enrollment__course__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
