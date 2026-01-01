from django.test import TestCase
from django.contrib.auth import get_user_model
from courses.models import Course
from .models import (Assignment, AssignmentSubmission, AssignmentSubmissionFile,
                     AssignmentGradeRubric, AssignmentSubmissionRubricScore)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AssignmentModelTestCase(TestCase):
    """Test cases for Assignment model"""

    def setUp(self):
        """Set up test data"""
        # Create a course
        self.course = Course.objects.create(
            name="Test Course",
            code="TEST101",
            description="Test course description"
        )
        
        # Create users
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            role="instructor"
        )
        
        # Create assignment
        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Test Assignment",
            description="Test description",
            instructions="Do this assignment",
            due_date=timezone.now() + timedelta(days=7),
            points=100,
            created_by=self.instructor
        )

    def test_assignment_creation(self):
        """Test assignment creation"""
        self.assertEqual(self.assignment.title, "Test Assignment")
        self.assertEqual(self.assignment.course, self.course)
        self.assertEqual(self.assignment.points, 100)

    def test_assignment_is_not_overdue(self):
        """Test if assignment is not overdue"""
        self.assertFalse(self.assignment.is_overdue())

    def test_assignment_days_until_due(self):
        """Test days until due"""
        days = self.assignment.days_until_due()
        self.assertEqual(days, 7)

    def test_assignment_str(self):
        """Test assignment string representation"""
        expected = f"Test Assignment - {self.course.name}"
        self.assertEqual(str(self.assignment), expected)


class AssignmentSubmissionTestCase(TestCase):
    """Test cases for AssignmentSubmission model"""

    def setUp(self):
        """Set up test data"""
        self.course = Course.objects.create(
            name="Test Course",
            code="TEST101"
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            role="instructor"
        )
        
        self.student = User.objects.create_user(
            email="student@test.com",
            password="testpass123",
            role="student"
        )
        
        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Test Assignment",
            description="Test",
            instructions="Instructions",
            due_date=timezone.now() + timedelta(days=7),
            points=100,
            created_by=self.instructor
        )
        
        self.submission = AssignmentSubmission.objects.create(
            assignment=self.assignment,
            student=self.student,
            submission_text="My answer"
        )

    def test_submission_creation(self):
        """Test submission creation"""
        self.assertEqual(self.submission.student, self.student)
        self.assertEqual(self.submission.assignment, self.assignment)
        self.assertEqual(self.submission.submission_text, "My answer")

    def test_submission_is_not_late(self):
        """Test if submission is not late"""
        self.assertFalse(self.submission.is_late)

    def test_unique_submission_constraint(self):
        """Test unique constraint on (assignment, student)"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AssignmentSubmission.objects.create(
                assignment=self.assignment,
                student=self.student,
                submission_text="Another answer"
            )
