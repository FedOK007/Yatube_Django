from django.conf import settings
from django.test import TestCase

from ..models import Comment, Group, Post, User
from ..models import CROP_LEN_TEXT


CROP_LEN_TEXT = settings.CROP_LEN_TEXT


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_usr')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Т' * CROP_LEN_TEXT * 2,
            author=PostModelTests.user,
            group=PostModelTests.group
        )
        cls.comment = Comment.objects.create(
            text='C' * CROP_LEN_TEXT * 2,
            author=PostModelTests.user,
            post=cls.post,
        )

    def test_models_have_correct_object_names(self):
        object_str = {
            PostModelTests.post: 'Т' * CROP_LEN_TEXT,
            PostModelTests.group: 'Тестовая группа',
            PostModelTests.comment: 'C' * CROP_LEN_TEXT,
        }
        for object_item, expected_value in object_str.items():
            with self.subTest(object_item=object_item):
                self.assertEqual(str(object_item), expected_value)

    def test_verbose_name(self):
        verbose_name = {
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTests.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_help_text(self):
        help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTests.post._meta.get_field(field).help_text,
                    expected_value,
                )
