import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.conf import settings as djoser_settings
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.constants import field_error_message
from recipes.models import (Favorites, Ingredient, IngredientRecipe,
                            InShoppingCart, Recipe, Subscribe, Tag)

from .paginators import SubscriptionsRecipesPaginator

User = get_user_model()


def create_many_objects(data, recipe_id):
    queryset = []
    for item in data:
        obj = IngredientRecipe(
            recipe_id=recipe_id,
            ingredient_id=item.get('id'),
            amount=item.get('amount'),
        )
        queryset.append(obj)
    IngredientRecipe.objects.bulk_create(queryset)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов, с коротким телом ответа"""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class SpecialUserSerializer(UserSerializer):
    """Сериализатор для объекта пользователя"""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.BooleanField(required=False,
                                             default=False)

    class Meta:
        model = User
        fields = (djoser_settings.USER_ID_FIELD,
                  djoser_settings.LOGIN_FIELD,
                  ) + tuple(User.REQUIRED_FIELDS) + ('avatar', 'is_subscribed')
        read_only_fields = (djoser_settings.LOGIN_FIELD,)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('is_subscribed',) is None:
            representation['is_subscribed'] = False
        return representation


class SubscribeSerializer(SpecialUserSerializer):
    """Сериализатор для системы подписок"""

    recipes = serializers.SerializerMethodField('paginate_recipes')
    recipes_count = serializers.IntegerField()

    class Meta:
        model = SpecialUserSerializer.Meta.model
        fields = SpecialUserSerializer.Meta.fields
        fields += ('recipes', 'recipes_count')
        read_only_fields = SpecialUserSerializer.Meta.read_only_fields

    def paginate_recipes(self, obj):
        """добавляет пагинацию для списка рецептов"""
        request = self.context.get('request')
        paginator = SubscriptionsRecipesPaginator()
        page = paginator.paginate_queryset(obj.recipes.all().order_by('-id'),
                                           request)
        serializer = ShortRecipeSerializer(page, many=True)
        return serializer.data

    def validate(self, attrs):
        follower = attrs
        user = self.context.get('request').user
        if follower.id == user.id:
            raise ValidationError(
                'Нельзя подписасться на самого себя.'
            )
        return follower

    def save(self, validated_data):
        follower = validated_data
        user = self.context.get('request').user
        obj, created = Subscribe.objects.get_or_create(
            user=user,
            follower=follower
        )
        if not created:
            raise ValidationError(
                'Невозможно дважды подписаться на пользователя.')
        follower.is_subscribed = True
        return follower

    def to_internal_value(self, data):
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'

    def to_internal_value(self, data):
        return data


class CreateTagSerializer(serializers.ModelSerializer):
    """Сериализатор для проверки тэгов в рецепте"""
    id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())

    class Meta:
        model = Tag
        fields = ('id',)

    def to_internal_value(self, data):
        data = {'id': data}
        return super().to_internal_value(data)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = Ingredient
        fields = ('amount', 'id')


class SpecialIngredientSerializer(serializers.ModelSerializer):
    """специализированый сериализатор для ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        read_only=True, source='ingredient')
    name = serializers.SlugRelatedField(
        source='ingredient', slug_field="name", read_only=True)
    measurement_unit = serializers.SlugRelatedField(
        slug_field="measurement_unit", read_only=True, source='ingredient')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)

    def to_internal_value(self, data):
        return data


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов, только для чтения."""
    author = SpecialUserSerializer(read_only=True)
    ingredients = SpecialIngredientSerializer(many=True,
                                              source='ingredientrecipe',
                                              required=True)
    tags = TagSerializer(many=True,
                         required=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.BooleanField(required=False)
    is_in_shopping_cart = serializers.BooleanField(required=False)

    def get_request(self):
        """Получение объекта запроса"""
        return self.context.get('request')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.get_request().user.is_authenticated:
            data['is_favorited'] = Favorites.objects.filter(
                user=self.get_request().user,
                recipe_id=data['id']
            ).exists()
            data['is_in_shopping_cart'] = InShoppingCart.objects.filter(
                user=self.get_request().user,
                recipe_id=data['id']
            ).exists()
        return data

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'author',
                  'tags', 'ingredients', 'image',
                  'cooking_time', 'is_favorited', 'is_in_shopping_cart')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов"""

    author = SpecialUserSerializer(read_only=True)
    ingredients = SpecialIngredientSerializer(many=True,
                                              source='ingredientrecipe',
                                              required=True)
    tags = TagSerializer(many=True,
                         required=True)
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_request(self):
        """Получение объекта запроса"""
        return self.context.get('request')

    def create(self, validated_data):
        request = self.get_request()
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredientrecipe')
        recipe = Recipe(**validated_data)
        recipe.author = request.user
        recipe.save()
        for tag in tags_data:
            recipe.tags.add(tag)
        create_many_objects(ingredients_data, recipe.id)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта"""

        ingredients = validated_data.pop('ingredientrecipe', None)
        tags = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        instance.ingredients.clear()
        create_many_objects(ingredients, instance.id)
        instance.tags.set(tags)
        return instance

    def validate(self, attrs):
        """Валидация данных"""
        ingredients = attrs.get('ingredientrecipe', None)
        tags = attrs.get('tags', None)
        if ingredients is None or len(ingredients) == 0:
            raise ValidationError(field_error_message('ingredients'))
        list_of_id_ingredient = [item['id'] for item in ingredients]
        if len(list_of_id_ingredient) != len(set(list_of_id_ingredient)):
            raise ValidationError(
                'Нельзя использовать повторяющиеся ингредиенты.')
        ingredients = IngredientRecipeSerializer(data=ingredients, many=True)
        ingredients.is_valid(raise_exception=True)
        if tags is None or len(tags) == 0:
            raise ValidationError(field_error_message("tags"))
        list_of_tags_id = [item for item in tags]
        if len(list_of_tags_id) != len(set(list_of_tags_id)):
            raise ValidationError(
                'Нельзя использовать повторяющиеся тэги.')
        tags = CreateTagSerializer(data=tags, many=True,)
        tags.is_valid(raise_exception=True)
        return attrs


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для списка избранного."""

    id = serializers.IntegerField(source='recipe.id')
    name = serializers.StringRelatedField(source='recipe.name')
    image = serializers.StringRelatedField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favorites
        fields = ('id', 'name', 'image', 'cooking_time',)

    def get_request(self):
        """Получение объекта запроса."""
        return self.context.get('request')

    def create(self, validated_data):
        request = self.get_request()
        obj, created = self.Meta.model.objects.get_or_create(
            recipe=validated_data['recipe'], user=request.user)
        if not created:
            raise ValidationError('Невозможно добвать один рецепт дважды')
        return obj

    def to_internal_value(self, data):
        return data


class InShoppingCartSerializer(FavoritesSerializer):
    """Сериализатор для списка покупок"""

    class Meta:
        model = InShoppingCart
        fields = FavoritesSerializer.Meta.fields
