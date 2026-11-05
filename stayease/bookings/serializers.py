from rest_framework import serializers
from decimal import Decimal
from .models import Booking, Review
from hotels.models import Room


class BookingCreateSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    num_guests = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if attrs['check_in'] >= attrs['check_out']:
            raise serializers.ValidationError('check_out must be after check_in.')
        try:
            room = Room.objects.get(pk=attrs['room_id'], is_active=True)
        except Room.DoesNotExist:
            raise serializers.ValidationError('Room not found or not available.')
        if attrs['num_guests'] > room.max_occupancy:
            raise serializers.ValidationError(
                f"Room accommodates a maximum of {room.max_occupancy} guests."
            )
        return attrs


class BookingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.SerializerMethodField()
    room_number = serializers.SerializerMethodField()
    room_type = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'reference', 'user', 'room', 'hotel_name', 'room_number', 'room_type',
            'check_in', 'check_out', 'num_guests', 'status',
            'total_price', 'created_at', 'expires_at',
        ]

    def get_hotel_name(self, obj):
        return obj.room.hotel.name

    def get_room_number(self, obj):
        return obj.room.room_number

    def get_room_type(self, obj):
        return obj.room.room_type


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'booking', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value

    def validate(self, attrs):
        booking = attrs['booking']
        user = self.context['request'].user
        if booking.status != 'completed':
            raise serializers.ValidationError('Reviews can only be left for completed bookings.')
        if booking.user != user:
            raise serializers.ValidationError('You can only review your own bookings.')
        if hasattr(booking, 'review'):
            raise serializers.ValidationError('You have already reviewed this booking.')
        return attrs
