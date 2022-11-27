
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
CROP_LEN_TEXT = settings.CROP_LEN_TEXT


class CreateModel(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        abstract = True


class Group(models.Model):
    verbose_name = 'Группа'
    verbose_name_plural = 'Группы'
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
    )
    description = models.TextField(
        verbose_name='Описание',
    )

    def __str__(self):
        return self.title


class Post(CreateModel):
    verbose_name = 'Пост'
    verbose_name_plural = 'Посты'
    text = models.TextField(
        help_text='Введите текст поста',
        verbose_name='Текст поста',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Картинка',
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:CROP_LEN_TEXT]


class Comment(CreateModel):
    verbose_name = 'Комментарий'
    verbose_name_plural = 'Комментарии'
    text = models.TextField(
        help_text='Комментрий к посту',
        verbose_name='Комментарий',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:CROP_LEN_TEXT]


class Follow(models.Model):
    verbose_name = 'Подписка'
    verbose_name_plural = 'Подписки'
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписка',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='check_self_follow'
            )
        ]
