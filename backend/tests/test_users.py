from http import HTTPStatus

import pytest

from recipes.models import Subscribe

URL_TEMPLATE = '/api/users/'


@pytest.mark.django_db(transaction=True)
class TestUsers:

    def test_get_users_list(self, user_client, administrator, second_user,
                            user_superuser):
        response = user_client.get(f'{URL_TEMPLATE}')
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.json(), dict)
        assert 'results' in response.json()
        assert response.json()['count'] == 4

    def test_sign_up(self, anonymus_client):
        data = {
            "username": 'UserSignUp',
            "email": 'usersignup@yamdb.fake',
            "password": '13251325d',
            "first_name": 'test_first_name',
            "last_name": 'test_last_name'
        }
        response = anonymus_client.post(f'{URL_TEMPLATE}', data=data)
        assert response.status_code == HTTPStatus.CREATED
        assert 'username' in response.json()

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.CREATED),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_subscribe_to_user(
            self, client_fixture, expected_status, second_user):
        response = client_fixture.post(
            f'/api/users/{second_user.id}/subscribe/')
        assert response.status_code == expected_status
        if expected_status == HTTPStatus.CREATED:
            assert 'is_subscribed' in response.json()

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.NOT_FOUND),
        ],
    )
    def test_subscriptions(
            self, client_fixture, expected_status, second_user, user):
        Subscribe.objects.create(user=user, follower=second_user)
        response = client_fixture.get(f'{URL_TEMPLATE}subscriptions/')

        assert response.status_code == expected_status
        if expected_status == HTTPStatus.OK:
            assert response.json()['count'] == 1

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_users_me(self, user, client_fixture, expected_status):
        response = client_fixture.get(f'{URL_TEMPLATE}me/')
        assert response.status_code == expected_status
        if expected_status == HTTPStatus.OK:
            assert response.json()['username'] == user.username

    @pytest.mark.parametrize(
        "client_fixture",
        [
            (pytest.lazy_fixture("user_client")),
            (pytest.lazy_fixture("anonymus_client")),
        ],
    )
    def test_user_detail(self, client_fixture, second_user):
        response = client_fixture.get(f'{URL_TEMPLATE}{second_user.id}/')
        assert response.status_code == HTTPStatus.OK
        assert response.json()['username'] == second_user.username

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("admin_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("user_superuser_client"),
             HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_set_password(seld, client_fixture, expected_status):
        data = {
            "new_password": "13251325d",
            "current_password": "1234567"
        }
        response = client_fixture.post(f'{URL_TEMPLATE}set_password/',
                                       data=data)
        assert response.status_code == expected_status


@pytest.mark.django_db(transaction=True)
class TestAvatar:

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("admin_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("user_superuser_client"), HTTPStatus.OK),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_add_avatar(self, client_fixture, expected_status):
        data = {
            'avatar': "data:image/png;base64,iVBORw0KGgoAAAA"
            + "NSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/"
            + "S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAA"
            + "ggCByxOyYQAAAABJRU5ErkJggg=="
        }
        response = client_fixture.put(f'{URL_TEMPLATE}me/avatar/', data=data)
        assert response.status_code == expected_status
        if expected_status != HTTPStatus.UNAUTHORIZED:
            assert 'avatar' in response.json()

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            (pytest.lazy_fixture("user_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("admin_client"), HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("user_superuser_client"),
             HTTPStatus.NO_CONTENT),
            (pytest.lazy_fixture("anonymus_client"), HTTPStatus.UNAUTHORIZED),
        ],
    )
    def test_delete_avatar(self, client_fixture, expected_status):
        response = client_fixture.delete(f'{URL_TEMPLATE}me/avatar/')
        assert response.status_code == expected_status


@pytest.mark.django_db(transaction=True)
class TestAuth:

    def test_login(self, anonymus_client, user):
        data = {
            "email": "testuser@yamdb.fake",
            "password": "1234567"
        }
        response = anonymus_client.post('/api/auth/token/login/', data)
        assert response.status_code == HTTPStatus.OK
        assert 'auth_token' in response.json()

    def test_logout(self, user_client):
        response = user_client.post('/api/auth/token/logout/')
        assert response.status_code == HTTPStatus.NO_CONTENT
