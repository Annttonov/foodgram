from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag

BOOLEAN_CHOICES = (('0', 'False'), ('1', 'True'),)


class RecipeFilter(filters.FilterSet):
    """Фильтрующий класс для рецептов.

    tags - фильтрация по тэгам
    author - фильтрация по автору
    is_favorited - фильтрация по избранному
    is_in_shopping_cart - фильтрация по списку покупок
    """

    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all(),
                                             to_field_name='slug',)
    author = filters.CharFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='annotate_field_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='annotate_field_filter')

    def annotate_field_filter(self, queryset, name, value):
        return queryset.filter(**{str(name): bool(value)})

    class Meta:
        model = Recipe
        fields = ('tags', 'author',
                  'is_favorited', 'is_in_shopping_cart',)


class IngredientFilter(filters.FilterSet):
    """фильтрующий класс для ингредиентов

    name - фильтрация по названию ингредиента, чувствителен к регистру.
    """

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
