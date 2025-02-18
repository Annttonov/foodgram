import base64

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.core.files.base import ContentFile


from recipes.models import Ingredient, Tag, Recipe


@pytest.fixture
def anonymus_client():
    return APIClient()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_superuser(django_user_model):
    return django_user_model.objects.create_user(
        username='TestSuperuser',
        email='testsuperuser@yamdb.fake',
        password='1234567',
        first_name='test_first_name',
        last_name='test_last_name',
        is_superuser=True
    )


@pytest.fixture
def administrator(django_user_model):
    return django_user_model.objects.create_user(
        username='TestAdmin',
        email='testadmin@yamdb.fake',
        password='1234567',
        first_name='test_first_name',
        last_name='test_last_name',
        is_staff=True
    )


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username='TestUser',
        email='testuser@yamdb.fake',
        password='1234567',
        first_name='test_first_name',
        last_name='test_last_name'
    )


@pytest.fixture
def second_user(django_user_model):
    return django_user_model.objects.create_user(
        username='SecondTestUser',
        email='secondtestuser@yamdb.fake',
        password='1234567',
        first_name='second_test_first_name',
        last_name='second_test_last_name'
    )


@pytest.fixture
def token_user_superuser(user_superuser):
    token, _ = Token.objects.get_or_create(user=user_superuser)
    return {
        'access': str(token.key),
    }


@pytest.fixture
def user_superuser_client(api_client, token_user_superuser):
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Token {token_user_superuser["access"]}'
    )
    return api_client


@pytest.fixture
def token_admin(administrator):
    token, _ = Token.objects.get_or_create(user=administrator)
    return {
        'access': str(token.key),
    }


@pytest.fixture
def admin_client(api_client, token_admin):
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token_admin["access"]}')
    return api_client


@pytest.fixture
def token_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {
        'access': str(token.key),
    }


@pytest.fixture
def user_client(api_client, token_user):
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token_user["access"]}')
    return api_client


@pytest.fixture
def create_ingredients():
    ingradients_data = [
        {'id': 1,
         'name': 'первый ингредиент',
         'measurement_unit': 'гр'},
        {'id': 2,
         'name': 'второй ингредиент',
         'measurement_unit': 'мл'},
        {'id': 3,
         'name': 'третий ингредиент',
         'measurement_unit': 'шт'},
    ]
    for item in ingradients_data:
        ingredients = Ingredient(**item)
        ingredients.save()


@pytest.fixture
def create_tags():
    tags_data = [
        {'id': 1,
         'name': 'обед',
         'slug': 'dinner'},
        {'id': 2,
         'name': 'завтрак',
         'slug': 'breakfest'},
        {'id': 3,
         'name': 'супы',
         'slug': 'soups'},
    ]
    for item in tags_data:
        tags = Tag(**item)
        tags.save()


def decode(data):
    format, imgstr = data.split(';base64,')
    ext = format.split('/')[-1]

    return ContentFile(base64.b64decode(imgstr), name='temp.' + ext)


@pytest.fixture
def create_recipe(user, create_tags, create_ingredients):
    data = {
        "name": "Test Recipe",
        "ingredients": [
            {
                "id": Ingredient.objects.all().first().id,
                "amount": 100
            }
        ],
        "tags": [
            Tag.objects.all().first().id
        ],
        "text": "Test description",
        "cooking_time": 30,
        "image": decode(
            "data:image/png;base64,iVBORw0KGgoAAAA"
            + "NSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/"
            + "S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAA"
            + "ggCByxOyYQAAAABJRU5ErkJggg==")
    }
    ingredients = data.pop('ingredients')
    tags = data.pop('tags')
    recipe = Recipe(**data)
    recipe.author = user
    recipe.save()
    for tag in tags:
        recipe.tags.add(tag)
    for ingredient in ingredients:
        recipe.ingredients.add(
            ingredient['id'],
            through_defaults={'amount': ingredient['amount']}
        )
