from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
CROP_LEN_TEXT = 15


class CreateModel(models.Model):
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
    )

    class Meta:
        abstract = True


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(CreateModel):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста',
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
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta():
        ordering = ('-created',)

    def __str__(self):
        return self.text[:CROP_LEN_TEXT]


class Comment(CreateModel):
    text = models.TextField(
        'Комментарий',
        help_text='Комментрий к посту'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta():
        ordering = ('-created',)

    def __str__(self):
        return self.text[:CROP_LEN_TEXT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
