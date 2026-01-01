from rest_framework import permissions
from courses.models import Enrollment


class IsInstructor(permissions.BasePermission):
    """Permission for instructors"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'instructor'


class IsAdmin(permissions.BasePermission):
    """Permission for admins"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'admin'


class IsStudent(permissions.BasePermission):
    """Permission for students"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'student'


class CanCreateAssignment(permissions.BasePermission):
    """Only admins and instructors can create assignments"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role in ['admin', 'instructor']


class CanEditAssignment(permissions.BasePermission):
    """Only admins or assignment creator (instructor) can edit"""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'role'):
            return False
        if request.user.role == 'admin':
            return True
        if request.user.role == 'instructor' and obj.created_by == request.user:
            return True
        return False


class CanViewAssignment(permissions.BasePermission):
    """Students can view published assignments for their courses, instructors and admins can view all"""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'role'):
            return False
        
        # Admins can view all
        if request.user.role == 'admin':
            return True
        
        # Instructors can view all for their courses
        if request.user.role == 'instructor':
            return obj.created_by == request.user or obj.course.instructor == request.user
        
        # Students can view only published assignments for their enrolled courses
        if request.user.role == 'student':
            if not obj.is_published:
                return False
            return Enrollment.objects.filter(
                student=request.user,
                course=obj.course,
                status='active'
            ).exists()
        
        return False


class CanViewSubmission(permissions.BasePermission):
    """Students can view only their own, instructors can view from their courses, admins can view all"""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'role'):
            return False
        
        # Admins can view all
        if request.user.role == 'admin':
            return True
        
        # Instructors can view submissions from their courses
        if request.user.role == 'instructor':
            return obj.assignment.created_by == request.user or obj.assignment.course.instructor == request.user
        
        # Students can view only their own submissions
        if request.user.role == 'student':
            return obj.student == request.user
        
        return False


class CanGradeSubmission(permissions.BasePermission):
    """Only admins and the instructor who created the assignment can grade"""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'role'):
            return False
        
        # Admins can grade all
        if request.user.role == 'admin':
            return True
        
        # Instructors can grade submissions in their courses
        if request.user.role == 'instructor':
            return obj.assignment.created_by == request.user or obj.assignment.course.instructor == request.user
        
        return False


class CanSubmitAssignment(permissions.BasePermission):
    """Only enrolled students can submit"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'student'

    def has_object_permission(self, request, view, obj):
        """Check if student is enrolled in the course"""
        return Enrollment.objects.filter(
            student=request.user,
            course=obj.course,
            status='active'
        ).exists()


class CanEditSubmission(permissions.BasePermission):
    """Only the student who submitted can edit their own submission"""
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.student == request.user and not obj.is_graded
