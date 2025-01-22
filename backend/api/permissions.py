from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.author.id == request.user.id
                or request.method in SAFE_METHODS
                and request.user.is_)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_staff
                or request.method in SAFE_METHODS)