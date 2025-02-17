from http import HTTPStatus

import pytest


@pytest.mark.django_db
@pytest.mark.usefixtures('create_ingredients')
class TestIngredients:
    new_data = {
        'name': 'Новый ингредиент',
        'measurment_unit': 'новый юнит'
    }

    URL_TEMPLATE = '/api/ingredients'

    @pytest.mark.parametrize(
        "client_fixture",
        [
            (pytest.lazy_fixture("user_client")),
            (pytest.lazy_fixture("anonymus_client")),
        ],
    )
    def test_get_ingredients_list(self, client_fixture):
        response = client_fixture.get(f'{self.URL_TEMPLATE}/')
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.json(), list)
        response = client_fixture.get(
            f'{self.URL_TEMPLATE}/?name=первый ингредиент')
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.json(), list)
        assert 'первый ингредиент' in response.json()[0]['name']

    @pytest.mark.parametrize(
        "client_fixture",
        [
            (pytest.lazy_fixture("user_client")),
            (pytest.lazy_fixture("anonymus_client")),
        ],
    )
    def test_get_ingredient_detail(self, client_fixture):
        response = client_fixture.get(f'{self.URL_TEMPLATE}/1/')
        assert response.status_code == HTTPStatus.OK
        assert 'name' in response.json()
        assert 'measurement_unit' in response.json()

    @pytest.mark.parametrize(
        "client_fixture",
        [
            (pytest.lazy_fixture("user_client")),
            (pytest.lazy_fixture("admin_client")),
            (pytest.lazy_fixture("user_superuser_client")),
            (pytest.lazy_fixture("anonymus_client")),
        ],
    )
    def test_post_patch_put_delete_requests(self, client_fixture):
        response = client_fixture.post(f'{self.URL_TEMPLATE}/1/',
                                       data=self.new_data)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = client_fixture.put(f'{self.URL_TEMPLATE}/1/',
                                      data=self.new_data)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = client_fixture.patch(f'{self.URL_TEMPLATE}/1/',
                                        data=self.new_data)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = client_fixture.delete(f'{self.URL_TEMPLATE}/1/')
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
