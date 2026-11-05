from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookingListView.as_view(), name='booking-list'),
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('<int:pk>/cancel/', views.BookingCancelView.as_view(), name='booking-cancel'),
    path('reviews/', views.ReviewCreateView.as_view(), name='review-create'),
]
