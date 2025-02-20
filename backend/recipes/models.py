from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import SHORT_TITLE, STANDART_FIELD_LENGTH
from .validators import name_validator, username_validator


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(unique=True,
                              verbose_name='Эл. почта')
    username = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                verbose_name='Никнейм', unique=True,
                                validators=[
                                    username_validator,
                                ])
    first_name = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                 verbose_name='Фамилия')
    avatar = models.ImageField(upload_to='users/avatars/', null=True,
                               verbose_name='Аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'], name='username-email')
        ]

    def __str__(self) -> str:
        return self.username


class NameModel(models.Model):
    """Абстрактная модель для общего поля name и сортировки"""

    name = models.CharField(max_length=STANDART_FIELD_LENGTH,
                            verbose_name='Наименование', db_index=True,
                            validators=[
                                name_validator,
                            ])

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name[:SHORT_TITLE]


class RecipeForeignModel(models.Model):
    """Абстрактная реляционная модель к Recipe"""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user-%(class)s')
        ]

    def __str__(self):
        return self.recipe.name[:SHORT_TITLE]


class UserForeigndModel(models.Model):
    """Абстрактная реляционная модель к User"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s'
    )

    class Meta:
        abstract = True


class Ingredient(NameModel):
    """Модель ингредиента"""

    measurement_unit = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                        verbose_name='Еденица измерения')

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = NameModel.Meta.ordering
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name=('name-measurement_unit')
            )
        ]


class Tag(NameModel):
    """Модель тэга"""

    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('slug',)


class Recipe(NameModel):
    """Модель рецепта"""

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        blank=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты',
        blank=False,
        through='IngredientRecipe'
    )
    image = models.ImageField(
        upload_to='reicpes/media/',
        verbose_name='Изображение',
    )
    text = models.TextField(verbose_name='Текст', blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления')

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = NameModel.Meta.ordering


class Subscribe(UserForeigndModel):
    """Реляционная модель Подписок (User to User)"""

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписка',
        related_name='followers'

    )

    def __str__(self):
        return self.follower.username

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('follower__first_name',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'follower'], name='user-follower'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('follower')),
                name='user_cannot_be_follower',
            )
        ]


class InShoppingCart(RecipeForeignModel, UserForeigndModel):
    """Реляционная модель списка покупок (User to Recipe)"""

    class Meta:
        verbose_name = 'Список рецептов пользователя'
        verbose_name_plural = 'Списки рецептов пользователя'
        constraints = RecipeForeignModel.Meta.constraints

    def __str__(self):
        return self.recipe.name


class Favorites(RecipeForeignModel, UserForeigndModel):
    """Реляционная модель списка избранного (User to Recipe)"""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = RecipeForeignModel.Meta.constraints


class IngredientRecipe(RecipeForeignModel):
    """Реляционная модель списка ингредиентов рецепта (Ingredient to Recipe)"""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipes_with_ingredient'
    )
    amount = models.PositiveSmallIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        default_related_name = 'ingredients_of_recipe'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'], name='recipe-ingredient')
        ]
