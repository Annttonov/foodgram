from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтрующий класс для рецептов.

    params: параметры запроса, по которым фильтруются данные.
        tags: фильтрация по тэгам
        author: фильтрация по автору
        is_favorited: фильтрация по избранному
        is_in_shopping_cart: фильтрация по списку покупок
    """

    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all(),
                                             to_field_name='slug',)
    author = filters.CharFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(
        field_name='favorites', method='annotate_field_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='inshoppingcart', method='annotate_field_filter')

    def annotate_field_filter(self, queryset, name, value):
        if self.request.user.is_anonymous:
            raise ValidationError('Чтобы просматривать этот список список, '
                                  + 'требуется авторизация.')
        filter_template = {f'{name}__user': self.request.user}
        if value:
            return queryset.filter(**filter_template)
        return queryset.exclude(**filter_template)

    class Meta:
        model = Recipe
        fields = ('tags', 'author',
                  'is_favorited', 'is_in_shopping_cart',)


class IngredientFilter(filters.FilterSet):
    """фильтрующий класс для ингредиентов

    params:
        name: фильтрация по названию ингредиента, чувствителен к регистру.
    """

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
