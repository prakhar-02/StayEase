from decimal import Decimal
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer, ReviewSerializer
from hotels.models import Room, RoomUnavailability
from payments.models import Payment


class BookingCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        check_in = data['check_in']
        check_out = data['check_out']

        # Lock the room row — prevents two simultaneous requests from both creating a booking
        try:
            room = Room.objects.select_for_update().get(pk=data['room_id'], is_active=True)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found or unavailable.'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()

        # Delete expired pending bookings for this room before checking conflicts
        Booking.objects.filter(room=room, status='pending', expires_at__lt=now).delete()

        # Check for overlapping confirmed/active-pending bookings
        conflict = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()

        if conflict:
            return Response(
                {'error': 'Room is not available for the selected dates.'},
                status=status.HTTP_409_CONFLICT,
            )

        # Check for admin-blocked periods
        unavailable = RoomUnavailability.objects.filter(
            room=room,
            start_date__lt=check_out,
            end_date__gt=check_in,
        ).exists()

        if unavailable:
            return Response(
                {'error': 'Room is not available for the selected dates.'},
                status=status.HTTP_409_CONFLICT,
            )

        nights = (check_out - check_in).days
        total_price = room.price_per_night * Decimal(nights)

        booking = Booking.objects.create(
            user=request.user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            num_guests=data['num_guests'],
            total_price=total_price,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        Payment.objects.create(booking=booking, amount=total_price)

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        if user.role in ('hotel_admin', 'super_admin'):
            Booking.objects.filter(
                room__hotel__admin=user, status='pending', expires_at__lt=now
            ).delete()
            return (
                Booking.objects.filter(room__hotel__admin=user)
                .select_related('user', 'room__hotel')
                .order_by('-created_at')
            )

        Booking.objects.filter(
            user=user, status='pending', expires_at__lt=now
        ).delete()
        return (
            Booking.objects.filter(user=user)
            .select_related('room__hotel', 'room')
            .order_by('-created_at')
        )


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        now = timezone.now()

        if user.role in ('hotel_admin', 'super_admin'):
            qs = Booking.objects.filter(room__hotel__admin=user).select_related('room__hotel')
        else:
            qs = Booking.objects.filter(user=user).select_related('room__hotel')

        booking = generics.get_object_or_404(qs, pk=self.kwargs['pk'])

        if booking.status == 'pending' and booking.expires_at and booking.expires_at < now:
            booking.delete()
            from rest_framework.exceptions import NotFound
            raise NotFound('Booking has expired.')

        return booking


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            booking = Booking.objects.select_for_update().get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status not in ('pending', 'confirmed'):
            return Response(
                {'error': f'Cannot cancel a {booking.status} booking.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        was_confirmed = booking.status == 'confirmed'
        booking.status = 'cancelled'
        booking.save()

        if was_confirmed:
            from bookings.tasks import process_refund
            process_refund.delay(booking.id)

        return Response({
            'message': 'Booking cancelled.',
            'refund_initiated': was_confirmed,
        })


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
