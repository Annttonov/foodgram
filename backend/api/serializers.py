import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserSerializer
from djoser.conf import settings as djoser_settings
from django.contrib.auth import get_user_model

from recipes.models import (
    Ingredient,
    Tag,
    Subscribe,
    Recipe,
    IngredientRecipe,
    Favorites,
    InShoppingCart
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class SpecialUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (djoser_settings.USER_ID_FIELD,
                  djoser_settings.LOGIN_FIELD,
                  ) + tuple(User.REQUIRED_FIELDS) + ('avatar', 'is_subscribed')
        read_only_fields = (djoser_settings.LOGIN_FIELD,)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        status = Subscribe.objects.filter(
            user=request.user.id,
            follower=obj.id
        ).exists()
        return status


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class SpecialIngredientSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)

    def get_id(self, obj):
        return obj.ingredient.id

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def to_internal_value(self, data):
        return data


class RecipeSerializer(serializers.ModelSerializer):
    author = SpecialUserSerializer(read_only=True)
    ingredients = SpecialIngredientSerializer(many=True,
                                              source='ingredientrecipe_set')
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_request(self):
        return self.context.get('request')

    def create_object_in_table(self, obj, model):
        request = self.get_request()
        status = model.objects.filter(
            user_id=request.user.id,
            recipe_id=obj.id
        ).exists()
        return status

    def get_fields(self):
        fields = super().get_fields()
        request = self.context['request']
        if request.method != 'GET':
            fields.pop('is_favorited')
            fields.pop('is_in_shopping_cart')
        return fields

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
        if validated_data.get('ingredientrecipe_set'):
            instance.ingredients.clear()
            for ingredient_data in validated_data.get('ingredientrecipe_set'):
                instance.ingredients.add(
                    ingredient_data['id'],
                    through_defaults={'amount': ingredient_data['amount']}
                )
        instance.tags.set(validated_data.get('tags', instance.tags))
        return instance

    def get_is_favorited(self, obj):
        return self.create_object_in_table(obj=obj, model=Favorites)

    def get_is_in_shopping_cart(self, obj):
        return self.create_object_in_table(obj=obj, model=InShoppingCart)


class FavoritesSerializer(serializers.ModelSerializer):
    id = serializers.StringRelatedField(source='recipe.id')
    name = serializers.StringRelatedField(source='recipe.name')
    image = serializers.StringRelatedField(source='recipe.image')
    cooking_time = serializers.StringRelatedField(source='recipe.cooking_time')

    class Meta:
        model = Favorites
        fields = ('id', 'name', 'image', 'cooking_time',)

    def get_request(self):
        return self.context.get('request')

    def create(self, validated_data):
        request = self.get_request()
        recipe_id = self.context.get('kwargs').get('pk')
        obj = self.Meta.model.objects.create(
            recipe_id=recipe_id, user_id=request.user.id)
        return obj


class ShopingCartSerializer(FavoritesSerializer):
    class Meta:
        model = InShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time',)
