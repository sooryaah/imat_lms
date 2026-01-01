from django.contrib import admin
from .models import Payment, RefundRequest


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'amount', 'status', 'razorpay_order_id', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at', 'completed_at']
    search_fields = ['user__email', 'course__title', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('User & Course', {
            'fields': ('user', 'course')
        }),
        ('Razorpay Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Payment Info', {
            'fields': ('amount', 'currency', 'status', 'payment_method', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ['payment', 'status', 'refund_amount', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at', 'processed_at']
    search_fields = ['payment__user__email', 'payment__course__title', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    
    fieldsets = (
        ('Refund Details', {
            'fields': ('payment', 'reason', 'status')
        }),
        ('Admin Actions', {
            'fields': ('admin_notes', 'refund_amount', 'razorpay_refund_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
