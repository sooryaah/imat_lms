from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to allow read access to anyone, but write access only to admins and instructors.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for admins and instructors
        return (request.user and request.user.is_authenticated and 
                (request.user.is_admin or request.user.is_instructor))


class IsEnrolledStudent(permissions.BasePermission):
    """
    Permission to check if user is enrolled in the course.
    """
    def has_object_permission(self, request, view, obj):
        # Admin has access to everything
        if request.user.is_admin:
            return True
        
        # Check if content/module belongs to an enrolled course
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module'):
            course = obj.module.course
        else:
            return False
        
        # Check enrollment
        from courses.models import Enrollment
        return Enrollment.objects.filter(
            user=request.user,
            course=course,
            is_active=True
        ).exists()


class IsAdminOrInstructor(permissions.BasePermission):
    """
    Permission to only allow admin and instructor users to access the view.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                (request.user.is_admin or request.user.is_instructor))


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.is_admin:
            return True
        
        # Owner has access
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False
