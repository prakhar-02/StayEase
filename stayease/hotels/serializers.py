from rest_framework import serializers
from .models import Hotel, Room, RoomUnavailability


class RoomUnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomUnavailability
        fields = ['id', 'start_date', 'end_date', 'reason']


class RoomSerializer(serializers.ModelSerializer):
    unavailabilities = RoomUnavailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'room_type', 'description',
            'price_per_night', 'max_occupancy', 'is_active', 'unavailabilities',
        ]
        read_only_fields = ['id']


class RoomSearchSerializer(serializers.ModelSerializer):
    """Lighter serializer used inside search results."""
    class Meta:
        model = Room
        fields = ['id', 'room_number', 'room_type', 'description', 'price_per_night', 'max_occupancy']


class HotelListSerializer(serializers.ModelSerializer):
    """Used for list endpoint — no nested rooms to keep it fast."""
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'city', 'state', 'star_rating', 'amenities', 'image']


class HotelSerializer(serializers.ModelSerializer):
    """Full detail serializer — includes active rooms."""
    rooms = serializers.SerializerMethodField()
    admin_name = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'description', 'address', 'city', 'state', 'country',
            'star_rating', 'amenities', 'image', 'admin', 'admin_name', 'rooms', 'created_at',
        ]
        read_only_fields = ['id', 'admin', 'admin_name', 'created_at']

    def get_rooms(self, obj):
        active_rooms = obj.rooms.filter(is_active=True)
        return RoomSerializer(active_rooms, many=True).data

    def get_admin_name(self, obj):
        return obj.admin.username if obj.admin else None
