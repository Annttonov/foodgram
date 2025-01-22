import csv

from rest_framework.decorators import action, permission_classes
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, permissions
from djoser.views import UserViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse

from recipes import models
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from . import serializers

User = get_user_model()


class IngredientViewSet(ModelViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
    permission_classes = (IsAdminOrReadOnly,)


class TagViewSet(ModelViewSet):
    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    permission_classes = (IsAdminOrReadOnly,)


class SpecialUserViewSet(UserViewSet):

    def get_current_user(self, *args, **kwargs):
        return get_object_or_404(User, username=self.request.user.username)

    @action(
        detail=True,
        methods=['delete', 'put',]
    )
    def avatar(self, request, *args, **kwargs):
        user = self.get_current_user()
        if request.method == 'PUT':
            avatar = {
                'avatar': request.data['avatar']
            }
            serializer = serializers.SpecialUserSerializer(
                request.user,
                data=avatar,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            user.avatar.delete()
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',))
    def subscriptions(self, request, *args, **kwargs):
        user = self.get_current_user()
        followers = user.followers.all()
        queryset = User.objects.all().filter(username__in=list(followers))
        print(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=('post', 'delete',))
    @permission_classes([permissions.IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        if request.method == 'POST':
            follower = models.Subscribe.objects.create(
                user=self.get_current_user(),
                follower=self.get_object()
            )
            serializer = serializers.SpecialUserSerializer(
                self.get_object(),
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        follower = get_object_or_404(
            models.Subscribe,
            user=self.get_current_user(),
            follower=self.get_object()
        )
        follower.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    serializer_class = serializers.RecipeSerializer
    queryset = models.Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = pass

    @action(methods=['post', 'delete'], detail=True,)
    def favorite(self, request, *args, **kwargs):
        return self.create_or_delete(request,
                                     models.Favorites,
                                     serializers.FavoritesSerializer,
                                     *args, **kwargs)

    @action(methods=['post', 'delete'], detail=True,)
    def shopping_cart(self, request, *args, **kwargs):
        return self.create_or_delete(request,
                                     models.InShoppingCart,
                                     serializers.ShopingCartSerializer,
                                     *args, **kwargs)

    def create_or_delete(
            self, request, model, serializer_class, *args, **kwargs):
        if request.method == 'POST':
            serializer = serializer_class(
                data=request.data, context={
                    'kwargs': self.kwargs,
                    'request': request})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers)
        model.objects.filter(
            recipe_id=self.kwargs.get('pk'),
            user_id=request.user.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',))
    def download_shopping_cart(self, request, *args, **kwargs):
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
        with open('media/shopping_cart/test.csv', 'w',
                  newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ('id', 'ingredient_name', 'measurement_unit', 'amount')
            writer.writerow(header)
            for row in rows.values():
                writer.writerow(row)
        return FileResponse(
            'media/shopping_cart/test.csv', 'rb',
            as_attachment=True,
            filename='test.csv',
        )
