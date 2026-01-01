from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, ModuleViewSet, ContentViewSet,
    QuizViewSet, QuestionViewSet, EnrollmentViewSet,
    ProgressViewSet, QuizAttemptViewSet, ReviewViewSet, ApplicationViewSet
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'contents', ContentViewSet, basename='content')
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'progress', ProgressViewSet, basename='progress')
router.register(r'quiz-attempts', QuizAttemptViewSet, basename='quiz-attempt')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)), 
]
