from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment
from assignments.models import Assignment
from .models import Notification, NotificationType, NotificationPreference, NotificationTemplate

User = get_user_model()


@receiver(post_save, sender=Course)
def notify_new_course(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a new course is created.
    Notifies all students or matching criteria based on preferences.
    """
    if not created or not instance.is_published:
        return

    try:
        notification_type = NotificationType.objects.get(name='new_course')
    except NotificationType.DoesNotExist:
        # If notification type doesn't exist, create it
        notification_type = NotificationType.objects.create(
            name='new_course',
            category='course',
            description='New course added to platform'
        )

    # Get all students
    all_students = User.objects.filter(role='student')

    # Filter students who want this notification
    for student in all_students:
        try:
            pref = student.notification_preference
            if not pref.notify_new_course:
                continue
        except NotificationPreference.DoesNotExist:
            # Create default preference if doesn't exist
            NotificationPreference.objects.create(user=student)

        # Get or create template
        try:
            template = NotificationTemplate.objects.get(
                notification_type=notification_type,
                name='new_course_default'
            )
            context = {
                'course_title': instance.title,
                'category': instance.category or 'General',
                'level': instance.get_level_display() if hasattr(instance, 'get_level_display') else instance.level,
                'price': instance.price
            }
            rendered = template.render(context)
        except NotificationTemplate.DoesNotExist:
            rendered = {
                'title': f"New Course: {instance.title}",
                'message': f"A new {instance.get_level_display() if hasattr(instance, 'get_level_display') else instance.level} course '{instance.title}' is now available!",
                'description': instance.description[:200]
            }

        # Create notification
        Notification.objects.create(
            notification_type=notification_type,
            user=student,
            title=rendered['title'],
            message=rendered['message'],
            description=rendered['description'],
            priority='medium',
            course=instance,
            action_url=f'/courses/{instance.id}/',
            is_sent=True
        )


@receiver(post_save, sender=Assignment)
def notify_new_assignment(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a new assignment is created.
    """
    if not created or not instance.is_published:
        return

    try:
        notification_type = NotificationType.objects.get(name='new_assignment')
    except NotificationType.DoesNotExist:
        notification_type = NotificationType.objects.create(
            name='new_assignment',
            category='assignment',
            description='New assignment added to course'
        )

    # Get all enrolled students
    enrolled_students = User.objects.filter(
        role='student',
        enrollments__course=instance.course
    ).distinct()

    for student in enrolled_students:
        try:
            pref = student.notification_preference
            if not pref.notify_new_assignment:
                continue
        except NotificationPreference.DoesNotExist:
            NotificationPreference.objects.create(user=student)

        Notification.objects.create(
            notification_type=notification_type,
            user=student,
            title=f"New Assignment: {instance.title}",
            message=f"A new assignment '{instance.title}' has been added to {instance.course.title}",
            description=instance.description[:200] if instance.description else "",
            priority='high',
            course=instance.course,
            related_object_id=instance.id,
            related_object_type='assignment',
            action_url=f'/courses/{instance.course.id}/assignments/{instance.id}/',
            is_sent=True
        )


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """
    Signal handler to create default notification preference for new users.
    """
    if created:
        NotificationPreference.objects.get_or_create(user=instance)
