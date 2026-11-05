from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # REST API
    path('api/auth/', include('users.urls')),
    path('api/hotels/', include('hotels.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/payments/', include('payments.urls')),

    # Frontend pages — served as Django templates, data loaded via JS + API
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('hotels/<int:pk>/', TemplateView.as_view(template_name='hotel_detail.html'), name='hotel-page'),
    path('booking/', TemplateView.as_view(template_name='booking_confirm.html'), name='booking-page'),
    path('payment/<int:booking_id>/', TemplateView.as_view(template_name='payment.html'), name='payment-page'),
    path('bookings/history/', TemplateView.as_view(template_name='booking_history.html'), name='history-page'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login-page'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register-page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
