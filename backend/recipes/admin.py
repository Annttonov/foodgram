from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, F
from rest_framework.authtoken.models import TokenProxy

from .constants import SHORT_TITLE
from .models import (Favorites, Ingredient, IngredientRecipe, InShoppingCart,
                     Recipe, Subscribe, Tag)

User = get_user_model()


class CustomModelAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)

    @admin.display(description='Наименование')
    def short_name(self, obj):
        if len(obj.name) <= 25:
            return f'{obj.name[:25]}...'
        return obj.name


class IngredientInLine(admin.StackedInline):
    model = IngredientRecipe
    extra = 1


class FavoriteInLine(admin.StackedInline):
    model = Favorites
    extra = 1


class InShoppingCartInLine(admin.StackedInline):
    model = InShoppingCart
    extra = 1


class SubscribeInLine(admin.StackedInline):
    model = Subscribe
    extra = 1
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email',)
    search_fields = ('username', 'email',)
    inlines = (
        FavoriteInLine,
        InShoppingCartInLine,
        SubscribeInLine,
    )


@admin.register(Recipe)
class RecipeAdmin(CustomModelAdmin):
    list_display = ('id', 'name', 'short_text', 'author',)
    search_fields = ('author', 'name',)
    readonly_fields = ['count_in_favorite',]
    ordering = ('-id',)
    inlines = (
        IngredientInLine,
    )
    list_filter = ('tags',)
    list_display_links = ('name',)

    @admin.display(description='Текст')
    def short_text(self, obj):
        if len(obj.text) <= SHORT_TITLE:
            return obj.text
        return f'{obj.text[:SHORT_TITLE]}...'

    def get_queryset(self, request):
        queryset = super().get_queryset(request).annotate(
            count_recipe_in_favorite=Count(F('favorites')))
        return queryset

    @admin.display(description='Количество добавлений в избранное',
                   )
    def count_in_favorite(self, obj):
        return obj.count_recipe_in_favorite


@admin.register(Ingredient)
class IngredientAdmin(CustomModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    list_display_links = ('name',)


@admin.register(Tag)
class TagAdmin(CustomModelAdmin):
    list_display = ('id', 'slug', 'name',)
    list_display_links = ('slug', 'name')


def has_permission(request):
    return (request.user.is_active
            and (request.user.is_staff
                 or request.user.is_superuser))


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
admin.site.has_permission = has_permission
admin.site.check
admin.site.empty_value_display = 'Не задано.'
admin.site.site_title = "Администрирование"
admin.site.site_header = "Администрирование"
