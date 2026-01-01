from django.db import models

class FAQ(models.Model):
    """FAQ model to store predefined questions and answers for the chatbot"""
    
    question = models.CharField(max_length=500, unique=True)
    answer = models.TextField()
    category = models.CharField(
        max_length=100,
        choices=[
            ('enrollment', 'Course Enrollment'),
            ('lessons', 'Lessons & Downloads'),
            ('assignments', 'Assignments'),
            ('progress', 'Progress Tracking'),
            ('support', 'Support & Contact'),
            ('general', 'General'),
        ],
        default='general'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
    
    def __str__(self):
        return self.question
