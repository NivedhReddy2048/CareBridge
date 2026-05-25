from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from billing.services.payment_service import PaymentService
from api.v1.serializers.billing_serializers import CreateOrderSerializer, VerifyPaymentSerializer
from api.v1.permissions import IsPatient
import logging

logger = logging.getLogger(__name__)

@extend_schema(
    request=CreateOrderSerializer,
    responses={200: inline_serializer(
        name='CheckoutDataResponse',
        fields={
            'order_id': serializers.CharField(),
            'key': serializers.CharField(),
            'amount': serializers.IntegerField(),
            'currency': serializers.CharField()
        }
    )}
)
@api_view(['POST'])
@permission_classes([IsPatient])
def create_payment_session(request):
    serializer = CreateOrderSerializer(data=request.data)
    if serializer.is_valid():
        appointment_id = serializer.validated_data['appointment_id']
        try:
            service = PaymentService()
            checkout_data = service.create_checkout_session(request.user, appointment_id)
            return Response(checkout_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating API payment session: {str(e)}")
            return Response({"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=VerifyPaymentSerializer,
    responses={200: inline_serializer(
        name='VerifyPaymentResponse',
        fields={
            'status': serializers.CharField(),
            'transaction_id': serializers.IntegerField()
        }
    )}
)
@api_view(['POST'])
@permission_classes([IsPatient])
def verify_payment(request):
    serializer = VerifyPaymentSerializer(data=request.data)
    if serializer.is_valid():
        order_id = serializer.validated_data['razorpay_order_id']
        payment_id = serializer.validated_data['razorpay_payment_id']
        signature = serializer.validated_data['razorpay_signature']
        
        try:
            service = PaymentService()
            txn = service.verify_and_confirm_payment(order_id, payment_id, signature)
            return Response({"status": "success", "transaction_id": txn.id}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error verifying API payment: {str(e)}")
            return Response({"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
