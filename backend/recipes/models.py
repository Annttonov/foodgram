from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import SHORT_TITLE, STANDART_FIELD_LENGTH
from .validators import name_validator, username_validator


class User(AbstractUser):
    email = models.EmailField(unique=True,
                              verbose_name='Эл. почта')
    username = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                verbose_name='Никнейм', unique=True,
                                validators=[username_validator,])
    first_name = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                 verbose_name='Фамилия')
    avatar = models.ImageField(upload_to='users/avatars/', null=True,
                               default=None, verbose_name='Аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')

    def __str__(self) -> str:
        return self.username

    class Meta:
        unique_together = ('username', 'email')
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class NameModel(models.Model):
    name = models.CharField(max_length=STANDART_FIELD_LENGTH,
                            verbose_name='Наименование', db_index=True,
                            validators=[name_validator,])

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name[:SHORT_TITLE]


class RecipeForeignModel(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.recipe.name[:SHORT_TITLE]


class Ingredient(NameModel):
    measurement_unit = models.CharField(max_length=STANDART_FIELD_LENGTH,
                                        verbose_name='Еденица измерения')

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Tag(NameModel):
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class Recipe(NameModel):
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги',
        blank=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
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
    cooking_time = models.IntegerField(verbose_name='Время приготовления')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Пользователь',
    )
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписка',
    )

    def __str__(self):
        return self.follower.username

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'follower'], name='user-follower'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('follower')),
                name='user_cannot_be_follower',
            )
        ]


class InShoppingCart(RecipeForeignModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='in_shopping_cart'
    )

    class Meta:
        verbose_name = 'Список рецептов пользователя'
        verbose_name_plural = 'Списки рецептов пользователя'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='user-shopping_cart')
        ]

    def __str__(self):
        return self.recipe.name


class Favorites(RecipeForeignModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='user-favorites')
        ]


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'], name='recipe-ingredient')
        ]
