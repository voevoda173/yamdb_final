from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from reviews.validators import validate_year


class Category(models.Model):
    """Модель для создания категорий (типов) произведений
    («Фильмы», «Книги», «Музыка»).
    """
    name = models.CharField(
        verbose_name='Название категории',
        max_length=256,
    )
    slug = models.SlugField(
        verbose_name='Адрес категории',
        max_length=50,
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name', )
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'slug'], name='name_slug_unique_ctg')
        ]

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель для создания жанров."""
    name = models.CharField(
        verbose_name='Название жанра',
        max_length=256,
    )
    slug = models.SlugField(
        verbose_name='Адрес жанра',
        max_length=50,
    )

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name', )
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'slug'], name='name_slug_unique_gnr')
        ]

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель для создания произведений, к которым пишут отзывы."""
    name = models.CharField(
        verbose_name='Название произведения',
        max_length=256,
    )
    year = models.PositiveSmallIntegerField(
        verbose_name='Год выпуска',
        db_index=True,
        validators=[validate_year, ]
    )
    description = models.TextField(
        verbose_name='Описание',
        null=True,
        blank=True,
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        related_name='title_genre',
    )
    category = models.ForeignKey(
        Category,
        related_name='category',
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('-year',)

    def __str__(self):
        return self.name


class Review(models.Model):
    """Модель для отзыва."""
    text = models.TextField(verbose_name='Текст отзыва')
    pub_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор'
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    score = models.IntegerField(
        verbose_name='Оценка',
        validators=[
            MinValueValidator(
                limit_value=1, message='Оценка не может быть меньше 1'
            ),
            MaxValueValidator(
                limit_value=10, message='Оценка не может быть больше 10'
            )]
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ('-pub_date',)
        constraints = (
            models.UniqueConstraint(fields=('author', 'title'),
                                    name='unique_author_title'),
        )

    def __str__(self):
        return f'Произведение: {str(self.title)[:15]}, Автор: {self.author}'


class Comment(models.Model):
    """Модель для комментария к отзыву."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата добавления'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]
