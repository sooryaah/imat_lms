from rest_framework import serializers
from .models import Payment, RefundRequest
from courses.models import Course


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_email', 'course', 'course_title', 
                  'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
                  'amount', 'currency', 'status', 'payment_method', 
                  'error_message', 'created_at', 'completed_at']
        read_only_fields = ['user', 'razorpay_order_id', 'status', 'created_at', 'completed_at']


class CreateOrderSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    
    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value, is_published=True)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or not available for purchase")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    course_id = serializers.IntegerField()


class RefundRequestSerializer(serializers.ModelSerializer):
    payment_details = PaymentSerializer(source='payment', read_only=True)
    
    class Meta:
        model = RefundRequest
        fields = ['id', 'payment', 'payment_details', 'reason', 'status', 
                  'admin_notes', 'refund_amount', 'created_at', 'processed_at']
        read_only_fields = ['status', 'admin_notes', 'refund_amount', 
                           'razorpay_refund_id', 'processed_at']
