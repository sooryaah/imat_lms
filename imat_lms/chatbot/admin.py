from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Question & Answer', {
            'fields': ('question', 'answer')
        }),
        ('Organization', {
            'fields': ('category', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
