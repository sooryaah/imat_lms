from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (AssignmentViewSet, AssignmentSubmissionViewSet, AssignmentRubricViewSet)

router = DefaultRouter()
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'submissions', AssignmentSubmissionViewSet, basename='submission')
router.register(r'rubrics', AssignmentRubricViewSet, basename='rubric')

urlpatterns = [
    path('', include(router.urls)),
]
