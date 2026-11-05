from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Exists, OuterRef, Prefetch
from django.core.cache import cache

from .models import Hotel, Room, RoomUnavailability
from .serializers import (
    HotelSerializer, HotelListSerializer,
    RoomSerializer, RoomSearchSerializer, RoomUnavailabilitySerializer,
)
from .permissions import IsHotelAdminOrReadOnly


class HotelListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsHotelAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'city', 'state']
    ordering_fields = ['star_rating', 'created_at', 'name']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return HotelListSerializer
        return HotelSerializer

    def get_queryset(self):
        return Hotel.objects.select_related('admin').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(admin=self.request.user)


class HotelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HotelSerializer
    permission_classes = [IsHotelAdminOrReadOnly]

    def get_queryset(self):
        return Hotel.objects.prefetch_related(
            Prefetch('rooms', queryset=Room.objects.filter(is_active=True))
        ).select_related('admin')

    def perform_destroy(self, instance):
        cache.delete_pattern('search:*')
        instance.delete()

    def perform_update(self, serializer):
        cache.delete_pattern('search:*')
        serializer.save()


class HotelRoomListCreateView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsHotelAdminOrReadOnly]

    def get_queryset(self):
        return Room.objects.filter(
            hotel_id=self.kwargs['hotel_id'], is_active=True
        ).prefetch_related('unavailabilities').order_by('room_number')

    def perform_create(self, serializer):
        hotel = Hotel.objects.get(pk=self.kwargs['hotel_id'])
        serializer.save(hotel=hotel)
        cache.delete_pattern('search:*')


class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsHotelAdminOrReadOnly]

    def get_queryset(self):
        return Room.objects.filter(hotel_id=self.kwargs['hotel_id'])

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        cache.delete_pattern('search:*')


class RoomUnavailabilityListCreateView(generics.ListCreateAPIView):
    serializer_class = RoomUnavailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RoomUnavailability.objects.filter(room_id=self.kwargs['room_id'])

    def perform_create(self, serializer):
        room = Room.objects.get(pk=self.kwargs['room_id'])
        serializer.save(room=room)
        cache.delete_pattern('search:*')


class HotelSearchView(APIView):
    """
    GET /api/hotels/search/?city=Lucknow&check_in=2025-06-10&check_out=2025-06-13&guests=2
    Returns hotels that have at least one available room for the given criteria.
    Results cached in Redis for 5 minutes.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        city = request.query_params.get('city', '').strip()
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')
        guests = request.query_params.get('guests', 1)

        if not all([city, check_in, check_out]):
            return Response(
                {'error': 'city, check_in, and check_out are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            guests = int(guests)
        except ValueError:
            return Response({'error': 'guests must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"search:{city.lower()}:{check_in}:{check_out}:{guests}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        from bookings.models import Booking
        from django.utils import timezone

        now = timezone.now()

        # Expired pending bookings do not block availability
        conflicting_bookings = Booking.objects.filter(
            room=OuterRef('pk'),
            status__in=['pending', 'confirmed'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exclude(
            status='pending', expires_at__lt=now,
        )

        conflicting_unavail = RoomUnavailability.objects.filter(
            room=OuterRef('pk'),
            start_date__lt=check_out,
            end_date__gt=check_in,
        )

        available_rooms = Room.objects.filter(
            is_active=True,
            max_occupancy__gte=guests,
        ).exclude(
            Exists(conflicting_bookings)
        ).exclude(
            Exists(conflicting_unavail)
        )

        hotels = Hotel.objects.filter(
            city__iexact=city,
            rooms__in=available_rooms,
        ).distinct().select_related('admin')

        results = []
        for hotel in hotels:
            hotel_rooms = list(available_rooms.filter(hotel=hotel))
            room_data = RoomSearchSerializer(hotel_rooms, many=True).data
            results.append({
                'id': hotel.id,
                'name': hotel.name,
                'city': hotel.city,
                'state': hotel.state,
                'star_rating': hotel.star_rating,
                'amenities': hotel.amenities,
                'image': request.build_absolute_uri(hotel.image.url) if hotel.image else None,
                'available_rooms': room_data,
                'min_price': str(min(r.price_per_night for r in hotel_rooms)),
            })

        cache.set(cache_key, results, timeout=300)
        return Response(results)
