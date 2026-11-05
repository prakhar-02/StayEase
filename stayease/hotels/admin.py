from django.contrib import admin
from .models import Hotel, Room, RoomUnavailability


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'star_rating', 'admin')
    list_filter = ('city', 'star_rating')
    search_fields = ('name', 'city')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'room_number', 'room_type', 'price_per_night', 'max_occupancy', 'is_active')
    list_filter = ('room_type', 'is_active', 'hotel')
    search_fields = ('hotel__name', 'room_number')


@admin.register(RoomUnavailability)
class RoomUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('room', 'start_date', 'end_date', 'reason')
