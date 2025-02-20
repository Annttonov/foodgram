import csv
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import Count, Exists, OuterRef, Subquery
from django.http import FileResponse
from django.http.response import Http404
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
    """Вьюсет для модели Ingredient."""

    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (permissions.AllowAny,)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""

    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    permission_classes = (permissions.AllowAny,)


class SpecialUserViewSet(UserViewSet):
    """Вьюсет для модели User."""

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
        """Получение объекта текущего пользователя."""

        return get_object_or_404(User, username=self.request.user.username)

    @action(
        detail=True,
        methods=[
            'delete',
            'put',
        ],
        permission_classes=(CurrentUserOrAdminOrReadOnly,)
    )
    def avatar(self, request, *args, **kwargs):
        """Добавление и удаление Аватара пользователя."""

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
        """Получение списка подписок пользователя."""

        user = self.get_current_user()
        followers = user.subscribe.all()
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
        """Подписаться на пользвателя."""

        obj = self.get_object()
        user = self.get_current_user()
        if request.method == 'POST':
            serializer = serializers.SubscribeSerializer(
                data=obj, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        try:
            get_object_or_404(
                models.Subscribe,
                user=user,
                follower=obj).delete()
        except Http404:
            raise ValidationError(
                f'Вы не подписаны на пользователя {obj.username}.')
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = models.Recipe.objects.prefetch_related(
        'ingredientrecipe', 'tags', 'ingredientrecipe__ingredient'
    ).select_related('author').order_by('-pk')
    serializer_class = serializers.RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = PageNumberCustomPaginator
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.ReadRecipeSerializer
        return super().get_serializer_class()

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,))
    def favorite(self, request, *args, **kwargs):
        """Добавление в избранное."""

        return self.create_or_delete(request,
                                     models.Favorites,
                                     serializers.FavoritesSerializer,
                                     *args, **kwargs)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=(
        permissions.IsAuthenticatedOrReadOnly,))
    def shopping_cart(self, request, *args, **kwargs):
        """Добавление в список покупок."""

        return self.create_or_delete(request,
                                     models.InShoppingCart,
                                     serializers.InShoppingCartSerializer,
                                     *args, **kwargs)

    def create_or_delete(self, request, Model,
                         serializer_class, *args, **kwargs):
        """Метод создания и удаления обЪекта.

        args:
            request: объект запроса.
            Model: Модель, объект которой требуется создать или удалить.
            serializer_class: ссылка на сериализатор для модели.

        returns:
            Response: объект ответа.
        """
        recipe = self.get_object()
        user = request.user
        self.check_object_permissions(request, recipe)
        if request.method == 'POST':
            serializer = serializer_class(
                data={'recipe': recipe}, context={
                    'request': request})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers)
        try:
            get_object_or_404(
                Model,
                recipe=recipe,
                user=user
            ).delete()
        except Http404:
            raise ValidationError('Такой рецепт не добавлен в список.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',),
            permission_classes=(
        permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        """Формирует и возвращает объект для скачивания."""

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
        os.makedirs('foodgram_media/shopping_cart', exist_ok=True)
        with open('foodgram_media/shopping_cart/shopping_cart.csv', 'w',
                  newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ('id', 'ingredient_name', 'measurement_unit', 'amount')
            writer.writerow(header)
            for row in rows.values():
                writer.writerow(row)
        return FileResponse(
            open('foodgram_media/shopping_cart/shopping_cart.csv', 'rb'),
            as_attachment=True,
            filename='shopping_cart.csv'
        )

    @action(detail=True, methods=('get',),
            permission_classes=[permissions.AllowAny],
            url_path='get-link')
    def get_link(self, request, *args, **kwargs):
        """Формируте и отдает URL рецепта"""

        url = self.request.get_raw_uri().split('/')
        url.pop(-2)
        url.pop(-4)
        url = str.join('/', url)
        url_data = {"short-link": url}
        return Response(url_data, status=status.HTTP_200_OK)
