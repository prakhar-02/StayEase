from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import User
from hotels.models import Hotel, Room


HOTELS = [
    {
        "name": "The Lucknow Grand",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "star_rating": 5,
        "description": "Heritage luxury near Hazratganj with award-winning Awadhi dining.",
        "address": "1 Vidhan Sabha Marg, Hazratganj, Lucknow",
        "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Gym", "Parking"],
        "rooms": [
            ("101", "single", "1800.00", 1),
            ("102", "double", "2600.00", 2),
            ("201", "deluxe", "4200.00", 3),
            ("301", "suite", "7500.00", 4),
        ],
    },
    {
        "name": "Riverside Inn",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "star_rating": 3,
        "description": "Budget-friendly stay on the Gomti riverfront, walkable to Marine Drive.",
        "address": "44 Riverbank Colony, Lucknow",
        "amenities": ["WiFi", "Restaurant", "Parking"],
        "rooms": [
            ("11", "single", "900.00", 1),
            ("12", "double", "1400.00", 2),
            ("14", "double", "1400.00", 2),
        ],
    },
    {
        "name": "Capital Court Delhi",
        "city": "Delhi",
        "state": "Delhi",
        "star_rating": 4,
        "description": "Business hotel in Connaught Place with metro access and 24x7 lounge.",
        "address": "P-12 Connaught Place, New Delhi",
        "amenities": ["WiFi", "Gym", "Restaurant", "Bar", "Airport Shuttle"],
        "rooms": [
            ("A1", "double", "3200.00", 2),
            ("A2", "deluxe", "4800.00", 3),
            ("B1", "suite", "9000.00", 4),
        ],
    },
    {
        "name": "Pink City Haveli",
        "city": "Jaipur",
        "state": "Rajasthan",
        "star_rating": 4,
        "description": "Restored haveli with courtyard, rooftop views of Nahargarh Fort.",
        "address": "7 Amer Road, Jaipur",
        "amenities": ["WiFi", "Pool", "Restaurant", "Heritage Tour", "Parking"],
        "rooms": [
            ("101", "double", "2800.00", 2),
            ("102", "deluxe", "4000.00", 3),
            ("103", "suite", "6500.00", 4),
        ],
    },
    {
        "name": "Goa Palm Beach Resort",
        "city": "Goa",
        "state": "Goa",
        "star_rating": 5,
        "description": "Beachfront resort at Candolim with private cabanas and water sports.",
        "address": "Candolim Beach Road, North Goa",
        "amenities": ["WiFi", "Pool", "Spa", "Beach Access", "Bar", "Water Sports"],
        "rooms": [
            ("G1", "double", "5000.00", 2),
            ("G2", "deluxe", "7000.00", 3),
            ("G3", "suite", "12000.00", 5),
        ],
    },
]


class Command(BaseCommand):
    help = "Populate the database with demo hotels, rooms, and users for local development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing hotels and rooms before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            deleted, _ = Room.objects.all().delete()
            Hotel.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing hotels and rooms."))

        admin, created = User.objects.get_or_create(
            username="hoteladmin",
            defaults={"email": "hoteladmin@stayease.test", "role": "hotel_admin"},
        )
        if created:
            admin.set_password("demopass123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created hotel admin: hoteladmin / demopass123"))

        guest, created = User.objects.get_or_create(
            username="guest",
            defaults={"email": "guest@stayease.test", "role": "guest"},
        )
        if created:
            guest.set_password("demopass123")
            guest.save()
            self.stdout.write(self.style.SUCCESS("Created guest: guest / demopass123"))

        hotel_count = 0
        room_count = 0
        for spec in HOTELS:
            hotel, created = Hotel.objects.get_or_create(
                name=spec["name"],
                defaults={
                    "description": spec["description"],
                    "address": spec["address"],
                    "city": spec["city"],
                    "state": spec["state"],
                    "country": "India",
                    "star_rating": spec["star_rating"],
                    "amenities": spec["amenities"],
                    "admin": admin,
                },
            )
            if created:
                hotel_count += 1
            for number, rtype, price, occ in spec["rooms"]:
                _, r_created = Room.objects.get_or_create(
                    hotel=hotel,
                    room_number=number,
                    defaults={
                        "room_type": rtype,
                        "description": f"{rtype.title()} room at {hotel.name}.",
                        "price_per_night": Decimal(price),
                        "max_occupancy": occ,
                        "is_active": True,
                    },
                )
                if r_created:
                    room_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {hotel_count} new hotels, {room_count} new rooms. "
                f"Totals now — hotels: {Hotel.objects.count()}, rooms: {Room.objects.count()}."
            )
        )
