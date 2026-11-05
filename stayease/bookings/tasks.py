from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def cancel_expired_bookings():
    """Runs every 60 seconds via Celery Beat. Deletes unpaid bookings past their expiry window."""
    from bookings.models import Booking
    expired = Booking.objects.filter(status='pending', expires_at__lt=timezone.now())
    count = expired.count()
    expired.delete()
    return f'Deleted {count} expired bookings.'


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation(self, booking_id):
    """Sends a confirmation email after payment is verified."""
    from bookings.models import Booking
    try:
        booking = Booking.objects.select_related('user', 'room__hotel').get(pk=booking_id)
        subject = f'Booking Confirmed — {booking.room.hotel.name}'
        message = (
            f"Dear {booking.user.username},\n\n"
            f"Your booking is confirmed!\n\n"
            f"Booking Reference : {booking.reference}\n"
            f"Hotel             : {booking.room.hotel.name}\n"
            f"Room              : {booking.room.room_number} ({booking.room.get_room_type_display()})\n"
            f"Check-in          : {booking.check_in}\n"
            f"Check-out         : {booking.check_out}\n"
            f"Guests            : {booking.num_guests}\n"
            f"Total Amount      : ₹{booking.total_price}\n\n"
            f"Thank you for choosing StayEase!"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email])
        return f'Confirmation sent for booking {booking.reference}'
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_cancellation_email(self, booking_id):
    """Sends a cancellation + refund notification email."""
    from bookings.models import Booking
    try:
        booking = Booking.objects.select_related('user', 'room__hotel').get(pk=booking_id)
        subject = f'Booking Cancelled — {booking.room.hotel.name}'
        message = (
            f"Dear {booking.user.username},\n\n"
            f"Your booking has been cancelled.\n\n"
            f"Booking Reference : {booking.reference}\n"
            f"Hotel             : {booking.room.hotel.name}\n"
            f"Check-in          : {booking.check_in}\n"
            f"Check-out         : {booking.check_out}\n\n"
            f"A refund of ₹{booking.total_price} has been initiated "
            f"and will reflect in 5–7 business days.\n\n"
            f"Thank you for choosing StayEase."
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [booking.user.email])
        return f'Cancellation email sent for booking {booking.reference}'
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_refund(self, booking_id):
    """Initiates Razorpay refund after booking cancellation."""
    import razorpay
    from bookings.models import Booking
    try:
        booking = Booking.objects.get(pk=booking_id)
        payment = booking.payment

        if payment.status != 'success':
            return f'No successful payment to refund for booking {booking.reference}'

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.payment.refund(payment.razorpay_payment_id, {'amount': int(payment.amount * 100)})

        payment.status = 'refunded'
        payment.save()

        send_cancellation_email.delay(booking_id)
        return f'Refund processed for booking {booking.reference}'
    except Exception as exc:
        raise self.retry(exc=exc)
