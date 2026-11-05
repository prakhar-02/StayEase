from django.contrib import admin
from .models import Booking, Review


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'room', 'check_in', 'check_out', 'status', 'total_price')
    list_filter = ('status',)
    search_fields = ('reference', 'user__email')
    readonly_fields = ('reference', 'created_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
