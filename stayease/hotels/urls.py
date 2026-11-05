from django.urls import path
from . import views

urlpatterns = [
    path('', views.HotelListCreateView.as_view(), name='hotel-list-create'),
    path('search/', views.HotelSearchView.as_view(), name='hotel-search'),
    path('<int:pk>/', views.HotelDetailView.as_view(), name='hotel-detail'),
    path('<int:hotel_id>/rooms/', views.HotelRoomListCreateView.as_view(), name='hotel-room-list'),
    path('<int:hotel_id>/rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('rooms/<int:room_id>/unavailability/', views.RoomUnavailabilityListCreateView.as_view(), name='room-unavailability'),
]
