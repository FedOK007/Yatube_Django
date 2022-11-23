from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticUlrTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_user = User.objects.create_user(username='testing_user_1')
        cls.new_user_2 = User.objects.create_user(username='testing_user_2')
        cls.group = Group.objects.create(
            title='New test group',
            slug='test-slug',
            description='new test group description',
        )
        cls.post = Post.objects.create(
            text='test new post',
            author=StaticUlrTests.new_user,
            group=StaticUlrTests.group,
        )
        cls.public_urls_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/testing_user_1/': 'posts/profile.html',
            f'/posts/{StaticUlrTests.post.id}/': 'posts/post_detail.html',
        }
        cls.authorized_urls_names = {
            f'/posts/{StaticUlrTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.follow_urls_names = {
            f'/profile/{StaticUlrTests.new_user.username}/follow/': '',
            f'/profile/{StaticUlrTests.new_user.username}/unfollow/': '',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticUlrTests.new_user)

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_urls_exist_at_desired_location(self):
        check_urls = {
            **StaticUlrTests.public_urls_names,
            **StaticUlrTests.authorized_urls_names,
        }
        for address, templates_access in check_urls.items():
            with self.subTest(
                address=address,
                templates_access=templates_access
            ):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_check_unexisting_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_access_not_author_redirect(self):
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(StaticUlrTests.new_user_2)
        response = self.authorized_client_1.get(
            f'/posts/{StaticUlrTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/posts/{StaticUlrTests.post.id}/'
        )

    def test_urls_redirect_unauthorized(self):
        check_urls = {
            **StaticUlrTests.authorized_urls_names,
            f'/posts/{StaticUlrTests.post.id}/comment/': '',
            **StaticUlrTests.follow_urls_names,
        }
        for address, templates_access in check_urls.items():
            with self.subTest(
                address=address,
                templates_access=templates_access
            ):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response,
                    f'/auth/login/?next={address}',
                )

    def test_urls_uses_correct_template(self):
        check_urls = {
            **StaticUlrTests.public_urls_names,
            **StaticUlrTests.authorized_urls_names,
            '/unexisting_page/': 'core/404.html',
        }
        for address, templates_access in check_urls.items():
            with self.subTest(
                address=address,
                templates_access=templates_access
            ):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, templates_access)
