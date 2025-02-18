import csv

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.db.models import Count, Exists, OuterRef, Subquery, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdminOrReadOnly
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes import models

from . import serializers
from .filters import IngredientFilter, RecipeFilter
from .paginators import PageNumberCustomPaginator
from .permissions import IsAdminOrAuthorOrReadOnly

User = get_user_model()


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (permissions.AllowAny,)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    permission_classes = (permissions.AllowAny,)


class SpecialUserViewSet(UserViewSet):
    pagination_class = PageNumberCustomPaginator
    queryset = User.objects.all().order_by('username')

    def get_permissions(self):
        if 'users/me/' in self.request.path:
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            return super().get_queryset()
        queryset = super().get_queryset().annotate(
            is_subscribed=Exists(Subquery(
                models.Subscribe.objects.filter(
                    user=self.request.user,
                    follower=OuterRef('pk')
                ))),
            recipes_count=Count('recipes'))
        return queryset

    def get_current_user(self, *args, **kwargs):
        return get_object_or_404(User, username=self.request.user.username)

    @action(
        detail=True,
        methods=[
            'delete',
            'put',],
        permission_classes=(CurrentUserOrAdminOrReadOnly,)
    )
    def avatar(self, request, *args, **kwargs):
        user = self.get_current_user()
        if request.method == 'PUT':
            avatar = {
                'avatar': request.data.get('avatar')
            }
            if avatar['avatar'] is None:
                raise ValidationError('Поле "avatar" пусто.')
            serializer = serializers.SpecialUserSerializer(
                request.user,
                data=avatar,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            user.avatar.delete()
            serializer.save()
            avatar = {'avatar': serializer.data['avatar']}
            return Response(avatar, status.HTTP_200_OK)
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',),
            permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,))
    def subscriptions(self, request, *args, **kwargs):
        user = self.get_current_user()
        followers = user.followers.all()
        queryset = self.get_queryset().filter(
            username__in=list(followers)).order_by('username')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.SubscribeSerializer(
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=('post', 'delete',),
            permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,))
    @permission_classes([permissions.IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        obj = self.get_object()
        user = self.get_current_user()
        if request.method == 'POST':
            if obj.id == user.id:
                raise ValidationError(
                    'Нельзя подписасться на самого себя.'
                )
            try:
                models.Subscribe.objects.create(
                    user=user,
                    follower=obj)
            except IntegrityError as e:
                if 'UNIQUE constraint failed:' in str(e):
                    raise ValidationError(
                        'Невозможно добвать один рецепт дважды')
                else:
                    raise e
            obj.is_subscribed = True
            serializer = serializers.SubscribeSerializer(
                obj, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not models.Subscribe.objects.filter(
            user=user,
            follower=obj
        ).exists():
            raise ValidationError(
                f'Вы не подписаны на пользователя {obj.username}')
        follower = get_object_or_404(
            models.Subscribe,
            user=user,
            follower=obj
        )
        follower.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    queryset = models.Recipe.objects.prefetch_related(
        'ingredientrecipe_set', 'tags', 'ingredientrecipe_set__ingredient'
    ).select_related('author').order_by('-pk')
    serializer_class = serializers.RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberCustomPaginator
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        self.check_permissions(self.request)
        if isinstance(self.request.user, AnonymousUser):
            return super().get_queryset().annotate(
                is_favorited=Value(False),
                is_in_shopping_cart=Value(False))

        queryset = super().get_queryset().annotate(
            is_favorited=Exists(
                Subquery(models.Favorites.objects.filter(
                    recipe=OuterRef('pk'),
                    user=self.request.user))),
            is_in_shopping_cart=Exists(
                Subquery(models.InShoppingCart.objects.filter(
                    recipe=OuterRef('pk'),
                    user=self.request.user))))

        return queryset

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,))
    def favorite(self, request, *args, **kwargs):
        return self.create_or_delete(request,
                                     models.Favorites,
                                     'список избранного',
                                     *args, **kwargs)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,))
    def shopping_cart(self, request, *args, **kwargs):
        return self.create_or_delete(request,
                                     models.InShoppingCart,
                                     'список покупок',
                                     *args, **kwargs)

    def create_or_delete(self, request, Model, list_name, *args, **kwargs):
        recipe = self.get_object()
        user = request.user
        self.check_object_permissions(request, recipe)
        if request.method == 'POST':
            try:
                Model.objects.create(
                    recipe=recipe, user=user)
            except IntegrityError as e:
                if 'UNIQUE constraint failed:' in str(e):
                    raise ValidationError(
                        'Невозможно добвать один рецепт дважды')
                else:
                    raise e
            serializer = serializers.ShortRecipeSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        if not Model.objects.filter(recipe=recipe,
                                    user=user).exists():
            raise ValidationError(f'Такой рецепт не добавлен в {list_name}')
        obj = get_object_or_404(
            Model,
            recipe=recipe,
            user=user
        )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',),
            permission_classes=(
        permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        self.check_permissions(request)
        ingredients = models.InShoppingCart.objects.filter(
            user=request.user).select_related(
                'recipe').prefetch_related(
                    'ingredient', 'ingredientrecipe').values_list(
                        'recipe__ingredients__id',
                        'recipe__ingredients__name',
                        'recipe__ingredients__measurement_unit',
                        'recipe__ingredientrecipe__amount')
        rows = {}
        for ingredient in ingredients:
            ingredient = list(ingredient)
            id = ingredient[0]
            if rows.get(str(id), None):
                rows[str(id)][-1] += ingredient[-1]
            else:
                rows[str(id)] = ingredient
        with open('foodgram_media/shopping_cart.csv', 'w',
                  newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ('id', 'ingredient_name', 'measurement_unit', 'amount')
            writer.writerow(header)
            for row in rows.values():
                writer.writerow(row)
        return FileResponse(
            open('foodgram_media/shopping_cart.csv', 'rb'),
            as_attachment=True,
            filename='shopping_cart.csv'
        )

    @action(detail=True, methods=('get',),
            permission_classes=[permissions.AllowAny],
            url_path='get-link')
    def get_link(self, request, *args, **kwargs):
        url = self.request.get_raw_uri().split('/')
        url.pop(-2)
        url.pop(-4)
        url = str.join('/', url)
        url_data = {"short-link": url}
        return Response(url_data, status=status.HTTP_200_OK)
