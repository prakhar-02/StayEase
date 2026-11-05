from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsHotelAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ('hotel_admin', 'super_admin')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == 'super_admin':
            return True
        if hasattr(obj, 'admin'):
            return obj.admin == request.user
        if hasattr(obj, 'hotel'):
            return obj.hotel.admin == request.user
        return False


class IsHotelAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('hotel_admin', 'super_admin')
