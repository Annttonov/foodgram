from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router_v1 = DefaultRouter()
router_v1.register(r'ingredients', views.IngredientViewSet,
                   basename='ingredient')
router_v1.register(r'tags', views.TagViewSet, basename='tag')
router_v1.register(r'recipes', views.RecipeViewSet, basename='recipe')
router_v1.register('users', views.SpecialUserViewSet, basename='subscribe')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
