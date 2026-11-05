from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_reference', 'razorpay_order_id',
            'razorpay_payment_id', 'amount', 'currency', 'status',
            'created_at', 'updated_at',
        ]

    def get_booking_reference(self, obj):
        return str(obj.booking.reference)
