from django.db import models
from users.models import User


class Hotel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    star_rating = models.PositiveSmallIntegerField(default=3)
    amenities = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to='hotels/', blank=True, null=True)
    admin = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_hotels'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RoomType(models.TextChoices):
    SINGLE = 'single', 'Single'
    DOUBLE = 'double', 'Double'
    SUITE = 'suite', 'Suite'
    DELUXE = 'deluxe', 'Deluxe'


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=20, choices=RoomType.choices)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_occupancy = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hotel', 'room_number')

    def __str__(self):
        return f"{self.hotel.name} - Room {self.room_number}"


class RoomUnavailability(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='unavailabilities')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.room} blocked {self.start_date} to {self.end_date}"
