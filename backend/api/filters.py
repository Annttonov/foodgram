import django_filters

from recipes.models import Recipe

class RecipeFilter(django_filters):
    class Meta:
        model = Recipe
        fields = ()