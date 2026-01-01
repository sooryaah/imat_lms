from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, RefundRequestViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'refund-requests', RefundRequestViewSet, basename='refund-request')

urlpatterns = [
    path('', include(router.urls)),
]
