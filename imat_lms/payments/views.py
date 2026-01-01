from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import razorpay
import hmac
import hashlib

from .models import Payment, RefundRequest
from .serializers import (
    PaymentSerializer, CreateOrderSerializer, 
    VerifyPaymentSerializer, RefundRequestSerializer
)
from courses.models import Course, Enrollment


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for payments.
    Students can view their own payments.
    Admins can view all payments.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    @action(detail=False, methods=['post'])
    def create_order(self, request):
        """
        Create a Razorpay order for course purchase.
        
        Process:
        1. Validate course and check if already enrolled
        2. Create Razorpay order
        3. Save payment record in database
        4. Return order details to client
        """
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data['course_id']
        course = get_object_or_404(Course, id=course_id, is_published=True)
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=course, is_active=True).exists():
            return Response(
                {'error': 'You are already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize Razorpay client
        razorpay_key_id = settings.RAZORPAY_KEY_ID
        razorpay_key_secret = settings.RAZORPAY_KEY_SECRET
        
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        # Create order
        amount = int(float(course.price) * 100)  # Convert to paise
        currency = 'INR'
        
        try:
            razorpay_order = client.order.create({
                'amount': amount,
                'currency': currency,
                'payment_capture': 1
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to create order: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Save payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            razorpay_order_id=razorpay_order['id'],
            amount=course.price,
            currency=currency,
            status='pending'
        )
        
        return Response({
            'order_id': razorpay_order['id'],
            'amount': amount,
            'currency': currency,
            'key_id': razorpay_key_id,
            'course_title': course.title,
            'payment_id': payment.id
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """
        Verify Razorpay payment signature and create enrollment.
        
        Process:
        1. Verify payment signature
        2. Update payment status
        3. Create enrollment
        4. Return success response
        """
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        razorpay_order_id = serializer.validated_data['razorpay_order_id']
        razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
        razorpay_signature = serializer.validated_data['razorpay_signature']
        course_id = serializer.validated_data['course_id']
        
        # Get payment record
        payment = get_object_or_404(
            Payment,
            razorpay_order_id=razorpay_order_id,
            user=request.user,
            course_id=course_id
        )
        
        # Verify signature
        razorpay_key_secret = settings.RAZORPAY_KEY_SECRET
        
        generated_signature = hmac.new(
            razorpay_key_secret.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            payment.status = 'failed'
            payment.error_message = 'Invalid payment signature'
            payment.save()
            
            return Response(
                {'error': 'Payment verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update payment record
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.save()
        
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=payment.course,
            defaults={'is_active': True}
        )
        
        if not created:
            # Reactivate if previously inactive
            enrollment.is_active = True
            enrollment.save()
        
        return Response({
            'message': 'Payment successful and enrollment created',
            'payment_id': payment.id,
            'enrollment_id': enrollment.id,
            'course_id': payment.course.id,
            'course_title': payment.course.title
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def payment_failed(self, request, pk=None):
        """Mark a payment as failed"""
        payment = self.get_object()
        
        if payment.user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment.status = 'failed'
        payment.error_message = request.data.get('error_message', 'Payment failed')
        payment.save()
        
        return Response({
            'message': 'Payment marked as failed'
        }, status=status.HTTP_200_OK)


class RefundRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for refund requests"""
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return RefundRequest.objects.all()
        return RefundRequest.objects.filter(payment__user=user)

    def perform_create(self, serializer):
        """Create a refund request"""
        payment_id = self.request.data.get('payment_id')
        payment = get_object_or_404(Payment, id=payment_id, user=self.request.user)
        
        # Check if payment is completed
        if payment.status != 'completed':
            raise serializers.ValidationError('Can only request refund for completed payments')
        
        # Check if refund already exists
        if hasattr(payment, 'refund_request'):
            raise serializers.ValidationError('Refund request already exists for this payment')
        
        serializer.save(payment=payment)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve refund request - Admin only"""
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can approve refunds'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refund_request = self.get_object()
        
        if refund_request.status != 'pending':
            return Response(
                {'error': 'Can only approve pending refund requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize Razorpay client
        razorpay_key_id = settings.RAZORPAY_KEY_ID
        razorpay_key_secret = settings.RAZORPAY_KEY_SECRET
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        # Process refund
        try:
            refund = client.payment.refund(
                refund_request.payment.razorpay_payment_id,
                {
                    'amount': int(float(refund_request.payment.amount) * 100),  # Amount in paise
                    'speed': 'normal'
                }
            )
            
            refund_request.status = 'processed'
            refund_request.razorpay_refund_id = refund['id']
            refund_request.refund_amount = refund_request.payment.amount
            refund_request.processed_at = timezone.now()
            refund_request.save()
            
            # Update payment status
            refund_request.payment.status = 'refunded'
            refund_request.payment.save()
            
            # Deactivate enrollment
            enrollment = Enrollment.objects.filter(
                user=refund_request.payment.user,
                course=refund_request.payment.course
            ).first()
            
            if enrollment:
                enrollment.is_active = False
                enrollment.save()
            
            return Response({
                'message': 'Refund processed successfully',
                'refund_id': refund['id']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process refund: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject refund request - Admin only"""
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can reject refunds'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refund_request = self.get_object()
        
        if refund_request.status != 'pending':
            return Response(
                {'error': 'Can only reject pending refund requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = 'rejected'
        refund_request.admin_notes = request.data.get('admin_notes', '')
        refund_request.save()
        
        return Response({
            'message': 'Refund request rejected'
        }, status=status.HTTP_200_OK)
