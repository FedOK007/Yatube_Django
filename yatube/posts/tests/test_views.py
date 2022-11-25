import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User
from ..forms import CommentForm, PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_user_1 = User.objects.create_user(username='testing_user_1')
        cls.new_user_2 = User.objects.create_user(username='testing_user_2')
        cls.group_1 = Group.objects.create(
            title='New test group_1',
            slug='test-slug-1',
            description='new test group_1 description',
        )
        cls.group_2 = Group.objects.create(
            title='New test group_2',
            slug='test-slug-2',
            description='new test group_1 description',
        )
        cls.post_1 = Post.objects.create(
            text='test new post 1',
            author=cls.new_user_1,
            group=cls.group_1,
        )
        cls.post_2 = Post.objects.create(
            text='test new post 2',
            author=cls.new_user_2,
            group=cls.group_2,
        )
        cls.reverse_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group_1.slug},
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.new_user_1.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post_1.id},
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post_1.id},
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            'small.gif',
            small_gif,
            content_type='image/gif'
        )
        cls.post_with_image = Post.objects.create(
            text='test new post with image',
            author=cls.new_user_1,
            group=cls.group_1,
            image=cls.uploaded,
        )
        cls.pages_with_list_posts = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group_1.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.new_user_1.username}
            ),
        ]
        cls.pages_check_not_post = [
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group_2.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.new_user_2.username}
            ),
        ]
        cls.page_singl_post = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post_with_image.id},
        )
        cls.pages_with_post_form = {
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post_1.id},
            ): 'edit',
            reverse('posts:post_create'): 'create',
        }
        cls.page_post_without_comment = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsPagesTests.post_2.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.new_user_1)

    def test_correct_templates(self):
        for reverse_name, template in PostsPagesTests.reverse_names.items():
            with self.subTest(
                reverse_name=reverse_name,
                template=template,
            ):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_context_has_posts(self):
        for page in PostsPagesTests.pages_with_list_posts:
            with self.subTest(
                page=page
            ):
                response = self.authorized_client.get(page)
                page_obj = response.context.get('page_obj').object_list
                self.assertTrue(
                    all(isinstance(x, Post) for x in page_obj),
                    'В контексте передается не список Post'
                )
                self.assertIn(PostsPagesTests.post_with_image, page_obj)
                for post in page_obj:
                    if post == PostsPagesTests.post_with_image:
                        self.assertNotEqual(
                            post.image,
                            ''
                        )

    def test_page_context_singl_post(self):
        response = self.authorized_client.get(PostsPagesTests.page_singl_post)
        post = response.context.get('post')
        self.assertIsInstance(
            post,
            Post,
            'В контексте не передается объект Post'
        )
        self.assertEqual(
            post.id,
            PostsPagesTests.post_with_image.id
        )
        self.assertNotEqual(post.image, '')

    def test_page_context_form(self):
        for reverse_name, action in (
            PostsPagesTests.pages_with_post_form.items()
        ):
            with self.subTest(
                reverse_name=reverse_name
            ):
                response = self.authorized_client.get(reverse_name)
                form = response.context.get('form')
                self.assertIsInstance(
                    form,
                    PostForm,
                    'В контексте не передается форма forms.ModelForm',
                )
                self.assertIsInstance(
                    form.instance,
                    Post,
                    ('Форма редактирования не '
                     'соответствует модели Post'),
                )
                if action == 'create':
                    self.assertIsNone(
                        form.instance.id,
                        ('в форму создания передается '
                         'контекст для редактирования'),
                    )
                if action == 'edit':
                    self.assertIsNotNone(
                        form.instance.id,
                        ('в форму создания не передается '
                         'контекст для редактирования'),
                    )

    def test_check_new_post_on_pages(self):
        new_post = Post.objects.create(
            text='test new post check adding',
            author=PostsPagesTests.new_user_1,
            group=PostsPagesTests.group_1,
        )
        for page in PostsPagesTests.pages_with_list_posts:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                page_obj = response.context.get('page_obj').object_list
                self.assertIn(new_post, page_obj)

    def test_check_new_post_not_on_pages(self):
        new_post = Post.objects.create(
            text='test new post check adding',
            author=PostsPagesTests.new_user_1,
            group=PostsPagesTests.group_1,
        )
        for page in PostsPagesTests.pages_check_not_post:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                page_obj = response.context.get('page_obj').object_list
                self.assertNotIn(new_post, page_obj)

    def test_context_contain_form_comment(self):
        response = self.authorized_client.get(PostsPagesTests.page_singl_post)
        form = response.context.get('form')
        self.assertIsInstance(
            form,
            CommentForm,
            'В контексте не передается форма CommentForm(forms.ModelForm)',
        )
        self.assertIsInstance(
            form.instance,
            Comment,
            ('Форма редактирования не '
                'соответствует модели Comment'),
        )

    def test_context_create_new_comment(self):
        new_comment = Comment.objects.create(
            text='Comment test for post, check adding',
            author=PostsPagesTests.new_user_1,
            post=PostsPagesTests.post_with_image,
        )
        response = self.authorized_client.get(PostsPagesTests.page_singl_post)
        comments = response.context.get('page_obj').object_list
        self.assertIn(new_comment, comments)

    def test_context_comment_not_on_page(self):
        new_comment = Comment.objects.create(
            text='Comment test for post, check adding',
            author=PostsPagesTests.new_user_1,
            post=PostsPagesTests.post_1,
        )
        response = self.authorized_client.get(
            PostsPagesTests.page_post_without_comment
        )
        comments = response.context.get('page_obj').object_list
        self.assertNotIn(new_comment, comments)

    def test_cache_index_page(self):
        new_post = Post.objects.create(
            text='test cache',
            author=PostsPagesTests.new_user_1,
            group=PostsPagesTests.group_1,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        new_post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        posts_new = response.content
        self.assertEqual(posts, posts_new, 'cache не работает')
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        posts_new = response.content
        self.assertNotEqual(posts, posts_new, 'Сбрасывание кэша не работае')


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_user_1 = User.objects.create_user(username='testing_user_1')
        cls.new_user_2 = User.objects.create_user(username='testing_user_2')
        cls.group_1 = Group.objects.create(
            title='New test group_1',
            slug='test-slug-1',
            description='new test group_1 description',
        )
        cls.group_2 = Group.objects.create(
            title='New test group_2',
            slug='test-slug-2',
            description='new test group_1 description',
        )
        cls.POST_ON_PAGE = int(settings.POSTS_ON_PAGE)
        cls.COUNT_POSTS_USER_1 = int(cls.POST_ON_PAGE) * 2 - 1
        cls.COUNT_POSTS_USER_2 = int(cls.POST_ON_PAGE) * 2 - 1
        cls.COUNT_POSTS_GROUP_1 = cls.COUNT_POSTS_USER_1
        cls.COUNT_POSTS_GROUP_2 = cls.COUNT_POSTS_USER_2

        cls.posts = Post.objects.bulk_create(
            list(
                Post(
                    text=f'test new post user_1 {i}',
                    author=cls.new_user_1,
                    group=cls.group_1,
                ) for i in range(cls.COUNT_POSTS_USER_1)
            ) + list(
                Post(
                    text=f'test new post user_2 {i}',
                    author=cls.new_user_2,
                    group=cls.group_2,
                ) for i in range(cls.COUNT_POSTS_USER_2)
            )
        )
        cls.total_obj = {
            reverse('posts:index'): (
                cls.COUNT_POSTS_USER_1 + cls.COUNT_POSTS_USER_2
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group_1.slug},
            ): cls.COUNT_POSTS_GROUP_1,
            reverse(
                'posts:profile',
                kwargs={'username': cls.new_user_1.username}
            ): cls.COUNT_POSTS_USER_1,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorTests.new_user_1)

    def test_paginator_first_page(self):
        for reverse_name in PaginatorTests.total_obj:
            with self.subTest(
                reverse_name=reverse_name,
            ):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page_obj').object_list),
                    PaginatorTests.POST_ON_PAGE
                )

    def test_paginator_second_page(self):
        for reverse_name, total_count in PaginatorTests.total_obj.items():
            with self.subTest(
                reverse_name=reverse_name,
            ):
                if (
                    total_count - PaginatorTests.POST_ON_PAGE
                    < PaginatorTests.POST_ON_PAGE * 2
                ):
                    posts_on_second_page = (
                        total_count - PaginatorTests.POST_ON_PAGE
                    )
                else:
                    posts_on_second_page = PaginatorTests.POST_ON_PAGE

                response = self.authorized_client.get(
                    reverse_name + '?page=2'
                )
                self.assertEqual(
                    len(response.context.get('page_obj').object_list),
                    posts_on_second_page
                )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        users = [
            User.objects.create_user(
                username=f'testing_user_{i}'
            ) for i in range(1, 4)
        ]
        cls.new_user_1, cls.new_user_2, cls.new_user_3 = users
        cls.pages = {
            'profile': reverse(
                'posts:profile',
                kwargs={
                    'username': cls.new_user_2.username,
                }
            ),
            'follow_index': reverse('posts:follow_index'),
            'profile_follow': reverse(
                'posts:profile_follow',
                kwargs={
                    'username': cls.new_user_2.username
                }
            ),
            'profile_unfollow': reverse(
                'posts:profile_unfollow',
                kwargs={
                    'username': cls.new_user_2.username
                }
            )
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(FollowTest.new_user_1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(FollowTest.new_user_2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(FollowTest.new_user_3)

    def test_follow(self):
        response = self.authorized_client1.get(
            FollowTest.pages['profile_follow']
        )
        self.assertRedirects(
            response,
            FollowTest.pages['profile']
        )
        self.assertTrue(
            Follow.objects.filter(
                user=FollowTest.new_user_1,
                author=FollowTest.new_user_2
            ).exists()
        )
        response = self.authorized_client1.get(
            FollowTest.pages['profile_follow']
        )
        self.assertEqual(
            FollowTest.new_user_1.follower.count(),
            1,
            'Проверьте, что нельзя подписаться дважы'
        )
        response = self.authorized_client2.get(
            FollowTest.pages['profile_follow']
        )
        self.assertEqual(
            FollowTest.new_user_2.follower.count(),
            0,
            'Проверьте, что нельзя подписаться на самого себя'
        )

    def test_unfollow(self):
        self.authorized_client1.get(
            FollowTest.pages['profile_follow']
        )
        response = self.authorized_client1.get(
            FollowTest.pages['profile_unfollow']
        )
        self.assertRedirects(
            response,
            FollowTest.pages['profile']
        )
        self.assertFalse(
            Follow.objects.filter(
                user=FollowTest.new_user_1,
                author=FollowTest.new_user_2
            ).exists()
        )

    def test_new_post_follow(self):
        response = self.authorized_client1.get(
            FollowTest.pages['profile_follow']
        )
        new_post = Post.objects.create(
            text='testing following post',
            author=FollowTest.new_user_2,
        )
        response = self.authorized_client1.get(
            FollowTest.pages['follow_index']
        )
        self.assertIn(new_post, response.context.get('page_obj'))
        response = self.authorized_client3.get(
            FollowTest.pages['follow_index']
        )
        self.assertNotIn(new_post, response.context.get('page_obj'))
