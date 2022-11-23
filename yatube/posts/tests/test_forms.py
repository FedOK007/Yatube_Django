import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        print('TEMP_MEDIA_ROOT: ', TEMP_MEDIA_ROOT)

        super().setUpClass()
        cls.form = PostForm()
        cls.new_user_1 = User.objects.create_user(username='testing_user_1')
        cls.group_1 = Group.objects.create(
            title='New test group_1',
            slug='test-slug-1',
            description='new test group_1 description',
        )
        cls.post_1 = Post.objects.create(
            text='test initial post',
            author=cls.new_user_1,
            group=cls.group_1,
        )
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorize_client = Client()
        self.authorize_client.force_login(PostFormTest.new_user_1)

    def test_create_post(self):
        count_posts = Post.objects.count()
        form_data = {
            'text': 'new post from test_create_post',
            'group': PostFormTest.group_1.id,
        }
        response = self.authorize_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTest.new_user_1.username},
        ))
        self.assertEqual(Post.objects.count(), count_posts + 1)
        latest_post = (
            Post
            .objects
            .select_related('author', 'group')
            .order_by('-created')
            .first()
        )
        self.assertTrue(all([
            latest_post.text == form_data['text'],
            latest_post.group.id == form_data['group'],
            latest_post.author == PostFormTest.new_user_1,
        ]))

    def test_change_post(self):
        post = Post.objects.create(
            text='test new post',
            author=PostFormTest.new_user_1,
            group=PostFormTest.group_1,
        )
        count_posts = Post.objects.count()
        form_data = {
            'text': 'change_post',
            'group': PostFormTest.group_1.id,
        }
        response = self.authorize_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id},
        ))
        self.assertEqual(Post.objects.count(), count_posts)
        changed_post = Post.objects.get(id=post.id)
        self.assertEqual(
            changed_post.text, form_data['text']
        )

    def test_create_post_with_image(self):
        count_posts = Post.objects.count()
        form_data = {
            'text': 'new post from test_create_post',
            'group': PostFormTest.group_1.id,
            'image': PostFormTest.uploaded,
        }
        response = self.authorize_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTest.new_user_1.username},
        ))
        self.assertEqual(Post.objects.count(), count_posts + 1)

    def test_comment_post(self):
        count_comments = PostFormTest.post_1.comments.count()
        form_data = {
            'text': 'comment for post',
        }
        response = self.authorize_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTest.post_1.id},
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            PostFormTest.post_1.comments.count(),
            count_comments + 1
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostFormTest.post_1.id},
        ))
