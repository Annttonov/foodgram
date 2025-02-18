from djoser import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (obj.author.id == request.user.id
                or request.method in SAFE_METHODS
                and request.user.is_authenticated)


class IsAdminOrAuthorOrReadOnly(BasePermission):
    """Для аутентифицированных пользователей, имеющих статус администратора или
    автора, иначе только просмотр."""

    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_staff
            or request.user.is_superuser
            or obj.author == request.user)


class CurrentUserOrAdminOrReadOnly(permissions.CurrentUserOrAdminOrReadOnly):
    def has_permission(self, request, view):
        return True
