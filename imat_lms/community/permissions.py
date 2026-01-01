"""
Permission classes for community features.

Implements role-based access control for:
- Community groups (public/private/moderated)
- Discussion posts (student/instructor/admin)
- Chat messages
"""

from rest_framework import permissions
from .models import GroupMember


class IsCommunityMember(permissions.BasePermission):
    """
    Permission to check if user is an active member of a community group.
    """

    def has_object_permission(self, request, view, obj):
        # Community group permission check
        if hasattr(obj, 'members'):
            return obj.members.filter(
                user=request.user,
                is_active=True
            ).exists()
        
        # Discussion post permission check
        if hasattr(obj, 'community'):
            return obj.community.members.filter(
                user=request.user,
                is_active=True
            ).exists()
        
        # Chat message permission check
        if hasattr(obj, 'sender'):
            return obj.community.members.filter(
                user=request.user,
                is_active=True
            ).exists()
        
        return False


class IsCommunityInstructor(permissions.BasePermission):
    """
    Permission to check if user is an instructor of the course.
    Only instructors can moderate and manage community.
    """

    def has_object_permission(self, request, view, obj):
        # Get community object
        community = obj if hasattr(obj, 'members') else obj.community if hasattr(obj, 'community') else None
        
        if not community:
            return False

        # Check if user is instructor of the related course
        if request.user.role == 'instructor':
            membership = community.members.filter(user=request.user).first()
            return membership and membership.role in ['instructor', 'moderator']
        
        return request.user.is_staff or request.user.is_superuser


class CanEditOwnPost(permissions.BasePermission):
    """
    Permission to allow users to edit only their own posts.
    Instructors and admins can edit any post.
    """

    def has_object_permission(self, request, view, obj):
        # Allow edit for post author
        if obj.author == request.user:
            return True
        
        # Allow edit for moderators/instructors
        if hasattr(obj, 'community'):
            membership = obj.community.members.filter(user=request.user).first()
            if membership and membership.role in ['instructor', 'moderator']:
                return True
        
        # Allow edit for staff/superuser
        return request.user.is_staff or request.user.is_superuser


class CanDeleteOwnPost(permissions.BasePermission):
    """
    Permission to allow users to delete only their own posts.
    Instructors and admins can delete any post.
    """

    def has_object_permission(self, request, view, obj):
        # Allow delete for post author
        if obj.author == request.user:
            return True
        
        # Allow delete for moderators/instructors
        if hasattr(obj, 'community'):
            membership = obj.community.members.filter(user=request.user).first()
            if membership and membership.role in ['instructor', 'moderator']:
                return True
        
        # Allow delete for staff/superuser
        return request.user.is_staff or request.user.is_superuser


class CanModeratePost(permissions.BasePermission):
    """
    Permission for moderating posts (approval, rejection, flagging).
    Only instructors and moderators can moderate.
    """

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'community'):
            membership = obj.community.members.filter(user=request.user).first()
            if membership and membership.role in ['instructor', 'moderator']:
                return True
        
        return request.user.is_staff or request.user.is_superuser


class IsEnrolledInCourse(permissions.BasePermission):
    """
    Permission to check if user is enrolled in the course linked to the community.
    Prevents unenrolled users from joining or viewing private communities.
    """

    def has_object_permission(self, request, view, obj):
        from courses.models import Enrollment
        
        # Get course from community
        course = obj.course if hasattr(obj, 'course') else obj.community.course if hasattr(obj, 'community') else None
        
        if not course:
            return False
        
        # Check enrollment
        from django.utils import timezone
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            is_active=True
        ).first()
        
        if not enrollment:
            return False
        
        # Check if enrollment hasn't expired
        if enrollment.expiry_date and enrollment.expiry_date < timezone.now():
            return False
        
        return True


class CanJoinCommunity(permissions.BasePermission):
    """
    Combined permission for joining a community.
    User must be:
    1. Authenticated
    2. Enrolled in the course
    3. Not already a member
    """

    def has_object_permission(self, request, view, obj):
        from courses.models import Enrollment
        from django.utils import timezone
        
        # Check enrollment
        course = obj.course if hasattr(obj, 'course') else None
        if not course:
            return False
        
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            is_active=True
        ).first()
        
        if not enrollment:
            return False
        
        # Check if enrollment hasn't expired
        if enrollment.expiry_date and enrollment.expiry_date < timezone.now():
            return False
        
        # Check if not already a member
        if obj.members.filter(user=request.user, is_active=True).exists():
            return False
        
        return True
