```markdown
# Проект Foodgram

> Foodgram — это платформа для публикации рецептов.
> Пользователи могут делиться своими рецептами, добавлять их в избранное,
> подписываться на других пользователей и создавать списки покупок.

---

## Описание проекта:

Foodgram позволяет пользователям:
- Публиковать рецепты с фотографиями, описанием и списком ингредиентов.
- Добавлять рецепты в избранное и список покупок.
- Подписываться на других пользователей и следить за их рецептами.
- Скачивать список покупок в формате CSV.(в будущий версия будет добавлена поддрежка фоматов TXT/PDF)

```

---

## Стек технологий:

- Python 3.9
- Django 3.2
- Django REST Framework 3.12.4
- PostgreSQL
- Docker
- Nginx
- Gunicorn

---

## Как запустить проект:

### 1. Клонирование репозитория

Клонируйте репозиторий и перейдите в него:

```bash
git clone https://github.com/annttonov/foodgram.git
cd foodgram
```

### 2. Настройка окружения

Создайте файл `.env` в корневой директории проекта и заполните его необходимыми переменными окружения:

```bash
SECRET_KEY=your_secret_key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
DB_HOST=db
DB_PORT=5432
```

### 3. Запуск проекта с помощью Docker

Находясь в корневой директории, соберите и запустите контейнеры:
###### (если вы используете Linux или MacOS, перед каждой командой нужно указывать 'sudo')

```bash
docker compose -f docker-compose.production.yml up -d --build
```

После запуска контейнеров выполните миграции и соберите статические файлы:

```bash
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
docker compose -f docker-compose.production.yml exec backend cp -r /app/backend_static/. /backend_static/static/
```

### 4. Заполнение базы данных ингредиентами 

Для заполнения базы данных ингредиентами выполните следующие команды команды:
###### (если вы используете Linux или MacOS, перед каждой командой нужно указывать 'sudo')

Скопируйте файл с ингредиентами в docker-container

```bash
docker cp ./data/ingredients.csv foodgram-backend:/app
```

Выполните команду для заполнения базы данных ингредиентами.


```bash
docker compose -f docker-compose.production.yml exec backend python manage.py fill_db
```


Удалите файл с ингредиентами из контейнера, он больше не понадобится.


```bash
docker compose -f docker-compose.production.yml exec backend rm -f /app/ingredients.csv
```


---

## API Endpoints

### Пользователи

- **Регистрация пользователя**: `POST /api/users/`
- **Получение токена**: `POST /api/auth/token/login/`
- **Удаление токена**: `POST /api/auth/token/logout/`
- **Изменение пароля**: `POST /api/users/set_password/`
- **Получение профиля пользователя**: `GET /api/users/me/`
- **Подписка на пользователя**: `POST /api/users/{id}/subscribe/`
- **Отписка от пользователя**: `DELETE /api/users/{id}/subscribe/`
- **Получение списка подписок**: `GET /api/users/subscriptions/`

### Рецепты

- **Получение списка рецептов**: `GET /api/recipes/`
- **Создание рецепта**: `POST /api/recipes/`
- **Получение рецепта по ID**: `GET /api/recipes/{id}/`
- **Обновление рецепта**: `PATCH /api/recipes/{id}/`
- **Удаление рецепта**: `DELETE /api/recipes/{id}/`
- **Добавление рецепта в избранное**: `POST /api/recipes/{id}/favorite/`
- **Удаление рецепта из избранного**: `DELETE /api/recipes/{id}/favorite/`
- **Добавление рецепта в список покупок**: `POST /api/recipes/{id}/shopping_cart/`
- **Удаление рецепта из списка покупок**: `DELETE /api/recipes/{id}/shopping_cart/`
- **Скачивание списка покупок**: `GET /api/recipes/download_shopping_cart/`

### Ингредиенты

- **Получение списка ингредиентов**: `GET /api/ingredients/`
- **Получение ингредиента по ID**: `GET /api/ingredients/{id}/`

### Теги

- **Получение списка тегов**: `GET /api/tags/`
- **Получение тега по ID**: `GET /api/tags/{id}/`

---

## Примеры запросов к API

### Регистрация пользователя

```bash
POST /api/users/
{
  "email": "user@example.com",
  "username": "user",
  "first_name": "John",
  "last_name": "Doe",
  "password": "password123"
}
```

### Получение токена

```bash
POST /api/auth/token/login/
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Создание рецепта

```bash
POST /api/recipes/
{
  "name": "Pizza",
  "ingredients": [
    {
      "id": 1,
      "amount": 200
    }
  ],
  "tags": [1, 2],
  "image": "data:image/png;base64,...",
  "text": "Delicious pizza recipe",
  "cooking_time": 30
}
```

---

## Автор проекта

- [Даниил Антонов](https://github.com/Annttonov)
```