from rest_framework import serializers

class CreateOrderSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()

class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
