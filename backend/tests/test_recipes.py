from http import HTTPStatus

import pytest
from django.http import FileResponse

from recipes.models import Favorites, InShoppingCart, Recipe

URL_TEMPLATE = '/api/recipes'


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures('create_tags', 'create_ingredients')
class TestRecipes:

    data = {
        "name": "Test Recipe",
        "ingredients": [{"id": 1, "amount": 100}],
        "tags": [1],
        "text": "Test description",
        "cooking_time": 30,
        "image": "data:image/png;base64,iVBORw0KGgoAAAA"
        + "NSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/"
        + "S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAA"
        + "ggCByxOyYQAAAABJRU5ErkJggg=="
    }

    invalid_data = {
        "name": "Test Recipe",
        "ingredients": [{"id": 1, "amount": 100}],
        "tags": [],
        "text": "Test description",
        "cooking_time": 0,
    }

    new_data = {
        "name": "New test Recipe",
        "ingredients": [
            {
                "id": 1,
                "amount": 100
            },
            {
                "id": 2,
                "amount": 100
            }
        ],
        "tags": [1,
                 2],
        "text": "New test description",
        "cooking_time": 100,
        "image": "data:image/png;base64,iVBORw0KGgoAAAA"
        + "NSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/"
        + "S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAA"
        + "ggCByxOyYQAAAABJRU5ErkJggg==",
    }

    @pytest.fixture
    def recipe_pk(self, user, user_client):
        self.test_create_recipe(user_client, HTTPStatus.CREATED)
        return Recipe.objects.get(author=user).id

    @pytest.mark.parametrize(
        "client_fixture",
        [
            (pytest.lazy_fixture("user_client")),
            (pytest.lazy_fixture("anonymus_client")),
        ],
    )
    def test_get_recipes_list(self, user_client, client_fixture):
        self.test_create_recipe(user_client, HTTPStatus.CREATED)
        response = client_fixture.get(f'{URL_TEMPLATE}/')
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.json(), dict)
        assert 'results' in response.json()
        assert response.json().get('count') == 1

    def test_filtration(self, user, user_client):
        self.test_create_recipe(user_client, HTTPStatus.CREATED)
        response = user_client.get(f'{URL_TEMPLATE}/?tags=soups')
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['results']) == 0
        response = user_client.get(f'{URL_TEMPLATE}/?tags=soups&tags=dinner')
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['results']) == 1
        response = user_client.get(f'{URL_TEMPLATE}/?author={user.id}')
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['results']) == 1
        response = user_client.get(f'{URL_TEMPLATE}/?is_favorited=1')
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['results']) == 0

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.CREATED),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_create_recipe(self, client_fixture, expected_status):
        response = client_fixture.post(f'{URL_TEMPLATE}/',
                                       self.data, format='json')
        assert response.status_code == expected_status

        if expected_status == HTTPStatus.CREATED:
            response = client_fixture.post(
                f'{URL_TEMPLATE}/', self.invalid_data)
            assert response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("admin_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("user_superuser_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_put_and_patch_recipe_request(self, recipe_pk, user_client,
                                          client_fixture, expected_status):
        put_data = {"text": "New text"}
        response = user_client.put(f'{URL_TEMPLATE}/{recipe_pk}/',
                                   data=put_data)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        data = self.new_data
        response = client_fixture.patch(
            f'/api/recipes/{recipe_pk}/', data=data, format='json')
        assert response.status_code == expected_status
        if expected_status != HTTPStatus.UNAUTHORIZED:
            assert response.json().get('text') == "New test description"
            assert response.json().get('tags') == [{'id': 2,
                                                    'name': 'завтрак',
                                                    'slug': 'breakfest'},
                                                   {'id': 1,
                                                    'name': 'обед',
                                                    'slug': 'dinner'},]
            assert response.json().get('ingredients') == [
                {
                    'id': 1,
                    'amount': 100,
                    'measurement_unit': 'гр',
                    'name': 'первый ингредиент'},
                {
                    'amount': 100,
                    'id': 2,
                    'measurement_unit': 'мл',
                    'name': 'второй ингредиент'
                }]

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("admin_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("user_superuser_client"),
             HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_delete_resipe(self, recipe_pk, client_fixture, expected_status):
        response = client_fixture.delete(f'{URL_TEMPLATE}/{recipe_pk}/')
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "client_fixture",
        [
            (pytest.lazy_fixture("user_client")),
            (pytest.lazy_fixture("anonymus_client")),
        ],
    )
    def test_get_link(self, client_fixture, user_client):
        self.test_create_recipe(user_client, HTTPStatus.CREATED)
        response = client_fixture.get(f'{URL_TEMPLATE}/1/get-link/')
        assert response.status_code == HTTPStatus.OK
        assert '/recipes/1/' in response.json()["short-link"]
        assert 'get-link' not in response.json()["short-link"].split('/')
        assert 'api' not in response.json()["short-link"].split('/')


@pytest.mark.django_db
@pytest.mark.usefixtures('create_recipe')
class TestFavoriteAndShoppingCart:

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.CREATED),
            (pytest.lazy_fixture("client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    @pytest.mark.parametrize('model, url', ((Favorites, 'favorite'),
                                            (InShoppingCart, 'shopping_cart')))
    def test_add_in_favorite_and_shopping_cart(self, client_fixture, user,
                                               expected_status, model, url):
        pk = Recipe.objects.get(author=user).id
        response = client_fixture.post(f'{URL_TEMPLATE}/{pk}/{url}/')
        assert response.status_code == expected_status
        if expected_status == HTTPStatus.UNAUTHORIZED:
            assert model.objects.all().count() == 0
        else:
            assert model.objects.all().count() == 1

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    @pytest.mark.parametrize(
        'model, url',
        (
            (Favorites, 'favorite'),
            (InShoppingCart, 'shopping_cart')
        )
    )
    def test_delete_in_shopping_cart_and_favorite(
            self, client_fixture, expected_status, model, url, user):
        recipe = Recipe.objects.get(author=user)
        model.objects.create(user=user, recipe=recipe)
        response = client_fixture.delete(f'{URL_TEMPLATE}/1/{url}/')
        count_objects = 1 if expected_status == HTTPStatus.UNAUTHORIZED else 0
        assert response.status_code == expected_status
        assert model.objects.all().count() == count_objects

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_download_shopping_cart(self, user_client,
                                    client_fixture, expected_status, user):
        InShoppingCart.objects.create(user=user, recipe_id=1)
        response = client_fixture.get(
            f'{URL_TEMPLATE}/download_shopping_cart/')
        assert response.status_code == expected_status
        if expected_status == HTTPStatus.OK:
            assert type(response) is FileResponse
