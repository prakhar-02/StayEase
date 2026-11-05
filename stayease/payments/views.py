import razorpay
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Payment
from bookings.models import Booking


def get_razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CreateRazorpayOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        if not booking_id:
            return Response({'error': 'booking_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.get(pk=booking_id, user=request.user, status='pending')
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found or already processed.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if booking.expires_at and booking.expires_at < timezone.now():
            booking.delete()
            return Response(
                {'error': 'Booking has expired. Please create a new booking.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = booking.payment
        amount_paise = int(payment.amount * 100)

        try:
            client = get_razorpay_client()
            order = client.order.create({
                'amount': amount_paise,
                'currency': payment.currency,
                'receipt': str(booking.reference),
            })
        except Exception:
            return Response(
                {'error': 'Failed to create payment order. Check Razorpay API keys.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        payment.razorpay_order_id = order['id']
        payment.save()

        return Response({
            'order_id': order['id'],
            'amount': amount_paise,
            'currency': payment.currency,
            'booking_id': booking.id,
            'key': settings.RAZORPAY_KEY_ID,
        })


class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'error': 'Missing payment verification data.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = get_razorpay_client()
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            return Response({'error': 'Payment signature verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = 'success'
        payment.save()

        booking = payment.booking
        booking.status = 'confirmed'
        booking.save()

        from bookings.tasks import send_booking_confirmation
        send_booking_confirmation.delay(booking.id)

        return Response({
            'message': 'Payment verified. Booking confirmed.',
            'booking_reference': str(booking.reference),
        })


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    Razorpay calls this URL on payment events.
    In local dev, test via /api/payments/verify/ instead.
    In production, configure this URL in the Razorpay dashboard.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        if webhook_secret:
            import hmac
            import hashlib
            signature = request.headers.get('X-Razorpay-Signature', '')
            generated = hmac.new(
                webhook_secret.encode(),
                request.body,
                hashlib.sha256,
            ).hexdigest()
            if generated != signature:
                return Response({'error': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        event = request.data.get('event')

        if event == 'payment.captured':
            entity = request.data['payload']['payment']['entity']
            order_id = entity['order_id']
            payment_id = entity['id']
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                if payment.status != 'success':
                    payment.razorpay_payment_id = payment_id
                    payment.status = 'success'
                    payment.save()
                    payment.booking.status = 'confirmed'
                    payment.booking.save()
                    from bookings.tasks import send_booking_confirmation
                    send_booking_confirmation.delay(payment.booking.id)
            except Payment.DoesNotExist:
                pass

        elif event == 'payment.failed':
            order_id = request.data['payload']['payment']['entity']['order_id']
            try:
                payment = Payment.objects.get(razorpay_order_id=order_id)
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass

        return Response({'status': 'ok'})


class InitiateRefundView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(pk=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        payment = booking.payment
        if payment.status != 'success':
            return Response(
                {'error': 'No successful payment found to refund.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client = get_razorpay_client()
            refund = client.payment.refund(payment.razorpay_payment_id, {
                'amount': int(payment.amount * 100),
            })
            payment.status = 'refunded'
            payment.save()
            return Response({'message': 'Refund initiated.', 'refund_id': refund['id']})
        except Exception:
            return Response(
                {'error': 'Refund failed. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
