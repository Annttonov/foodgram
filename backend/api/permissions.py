from djoser import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnly(BasePermission):
    """Только для просмотра"""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


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
    """Изменение доступно только для объекта, изменять который может только
    текущий пользователь или администратор иначе, только просмотр"""

    def has_permission(self, request, view):
        return True
