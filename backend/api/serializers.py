import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.conf import settings as djoser_settings
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.constants import field_error_message
from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag

from .paginators import SubscriptionsRecipesPaginator

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class SpecialUserSerializer(UserSerializer):
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
    recipes = serializers.SerializerMethodField('paginate_recipes')
    recipes_count = serializers.IntegerField()

    def paginate_recipes(self, obj):
        request = self.context.get('request')
        paginator = SubscriptionsRecipesPaginator()
        page = paginator.paginate_queryset(obj.recipes.all().order_by('-id'),
                                           request)
        serializer = ShortRecipeSerializer(page, many=True)
        return serializer.data

    class Meta:
        model = SpecialUserSerializer.Meta.model
        fields = SpecialUserSerializer.Meta.fields
        fields += ('recipes', 'recipes_count')
        read_only_fields = SpecialUserSerializer.Meta.read_only_fields


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

    def to_internal_value(self, data):
        return data


class SpecialIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)

    def to_internal_value(self, data):
        return data


class RecipeSerializer(serializers.ModelSerializer):
    author = SpecialUserSerializer(read_only=True)
    ingredients = SpecialIngredientSerializer(many=True,
                                              source='ingredientrecipe_set')
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.BooleanField(read_only=True,
                                            required=False,
                                            default=False)
    is_in_shopping_cart = serializers.BooleanField(read_only=True,
                                                   required=False,
                                                   default=False)

    class Meta:
        model = Recipe
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=['name'],
                message='Нельзя создать два рецепта с одинаковым названием'
            )
        ]

    def get_request(self):
        return self.context.get('request')

    def create(self, validated_data):
        request = self.get_request()
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredientrecipe_set')
        recipe = Recipe(**validated_data)
        recipe.author = request.user
        recipe.save()
        for tag in tags_data:
            recipe.tags.add(tag)
        for ingredient_data in ingredients_data:
            recipe.ingredients.add(
                ingredient_data['id'],
                through_defaults={'amount': ingredient_data['amount']}
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()
        ingredients = validated_data.get('ingredientrecipe_set', None)
        instance.ingredients.clear()
        for ingredient_data in ingredients:
            instance.ingredients.add(
                ingredient_data['id'],
                through_defaults={'amount': ingredient_data['amount']}
            )
        tags = validated_data.get('tags', None)
        instance.tags.set(tags)
        return instance

    def validate(self, attrs):
        ingredients = attrs.get('ingredientrecipe_set', None)
        tags = attrs.get('tags', None)
        cooking_time = attrs.get('cooking_time', None)
        if ingredients is None or len(ingredients) == 0:
            raise ValidationError(field_error_message('ingredients'))
        else:
            for idx in range(0, len(ingredients)):
                current = ingredients[idx]
                if not Ingredient.objects.filter(
                        id=current['id']).exists():
                    raise ValidationError('Несуществующий ингредиент')
                elif idx != 0 and ingredients[idx - 1]['id'] == current['id']:
                    raise ValidationError(
                        'Нельзя использовать повторяющиеся ингредиенты.')
                if int(ingredients[idx]['amount']) <= 1:
                    raise ValidationError(
                        'Количество ингридента не может быть меньше 1')
        if tags is None or len(tags) == 0:
            raise ValidationError(field_error_message("tags"))
        else:
            for idx in range(0, len(tags)):
                current = tags[idx]
                if not Ingredient.objects.filter(
                        id=current).exists():
                    raise ValidationError('Несуществующий тэг')
                elif idx != 0 and tags[idx - 1] == current:
                    raise ValidationError(
                        'Нельзя использовать повторяющиеся тэги.')
        if cooking_time is None:
            raise ValidationError(field_error_message("cooking_time"))
        elif cooking_time == 0:
            raise ValidationError(
                'Время приготовления не может быть меньше 1')
        return attrs
