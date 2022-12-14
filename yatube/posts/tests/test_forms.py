import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
STORAGE_PLACE = Post.image.field.upload_to
USERNAME = 'auth'
FOLLOWER = 'follower'
SLUG = 'test-slug'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_posts', args=[SLUG])
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME})
PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', kwargs={'username': USERNAME})
LOGIN_URL = reverse('users:login')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateTestForms(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower_user = User.objects.create_user(username=FOLLOWER)
        cls.author = Client()
        cls.follower = Client()
        cls.not_auth = Client()
        cls.author.force_login(cls.user)
        cls.follower.force_login(cls.follower_user)
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        # cls.uploaded = SimpleUploadedFile(
        #     name='small.gif',
        #     content=SMALL_GIF,
        #     content_type='image/gif'
        # )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            pub_date='Тестовая дата',
            group=cls.group,
            # image=cls.uploaded
        )
        cls.new_group = Group.objects.create(
            title='Новая группа',
            slug='test-slug_new',
            description='Тестовое описание новой группы',
        )
        cls.CREATE_COMMENT_URL = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.EDIT_REDIRECT = f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_valid_form_add_new_post(self):
        """Отправка валидной формы создает новый пост"""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='posts/small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Пост создан для проверки',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.author.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            PROFILE_URL
        )
        post_count_after = Post.objects.all().count()
        self.assertEqual(0, post_count_after - 1)
        new_post = Post.objects.get()
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(
            new_post.image.name,
            f'{STORAGE_PLACE}{form_data["image"].name}'
        )

    def test_valid_form_edit_post(self):
        """Отправка валидной формы со страницы edit_post"""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        new_post_form = {
            'text': 'Измененный пост',
            'group': self.new_group.id,
            'image': uploaded
        }
        response = self.author.post(
            self.POST_EDIT_URL,
            new_post_form,
            follow=True
        )
        self.assertRedirects(
            response,
            self.POST_DETAIL_URL
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, new_post_form['text'])
        self.assertEqual(post.group.id, new_post_form['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image.name,
            f'{STORAGE_PLACE}{new_post_form["image"].name}'
        )

    def test_post_create_page_show_correct_context(self):
        """
        Шаблоны post_create и post_edit
        сформирован с правильным контекстом.
        """
        urls_cases = [
            CREATE_URL,
            self.POST_EDIT_URL
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for case in urls_cases:
            response = self.author.get(case)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_valid_form_add_new_comment(self):
        """Отправка валидной формы создает новый комментарий"""
        Comment.objects.all().delete()
        form_data = {
            'text': 'Комментарий создан для проверки',
        }
        self.author.post(
            self.CREATE_COMMENT_URL,
            data=form_data,
            follow=True
        )
        comment_count_after = Comment.objects.all().count()
        self.assertEqual(0, comment_count_after - 1)
        new_comment = Comment.objects.get()
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.post, self.post)
        self.assertEqual(new_comment.author, self.user)

    def test_add_comment_show_correct_context(self):
        """
        Шаблон add_comment
        сформирован с правильным контекстом.
        """
        response = self.author.get(CREATE_URL)
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_create_post_for_anonim_user(self):
        """Аноним не может создать пост."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data_post = {
            'text': 'Пост создан для проверки',
            'group': self.group.id,
            'image': uploaded
        }
        self.not_auth.post(
            CREATE_URL,
            data=form_data_post,
            follow=True
        )
        self.assertEqual(0, Post.objects.all().count())

    def test_create_comment_for_anonim_user(self):
        """Аноним не может создать комменатрий."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        Comment.objects.all().delete()
        form_data_comment = {
            'text': 'Комментарий создан для проверки',
        }
        self.not_auth.post(
            self.CREATE_COMMENT_URL,
            data=form_data_comment,
            follow=True
        )
        self.assertEqual(0, Comment.objects.all().count())

    def test_update_post_for_anonim_user(self):
        """Аноним или не автор не может отредактировать пост, а автор может."""
        cases = [
            [self.not_auth, self.EDIT_REDIRECT],
            [self.follower, self.POST_DETAIL_URL],
        ]
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        new_post_form = {
            'text': 'Измененный пост',
            'group': self.new_group.id,
            'image': uploaded
        }
        for client, redirect in cases:
            with self.subTest(client=client):
                response = client.post(
                    self.POST_EDIT_URL,
                    new_post_form,
                    follow=True
                )
                self.assertRedirects(
                    response,
                    redirect
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(post.author.id, self.post.author.id)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group.id, self.post.group.id)
                self.assertFalse(post.image.name)

    def test_update_post_for_author(self):
        """Автор может отредактировать свой пост."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        new_post_form = {
            'text': 'Измененный пост',
            'group': self.new_group.id,
            'image': uploaded
        }
        response = self.author.post(
            self.POST_EDIT_URL,
            new_post_form,
            follow=True
        )
        self.assertRedirects(
            response,
            self.POST_DETAIL_URL
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.author.id, self.post.author.id)
        self.assertEqual(post.text, new_post_form['text'])
        self.assertEqual(post.group.id, new_post_form['group'])
        self.assertEqual(
            post.image.name,
            f'{STORAGE_PLACE}{new_post_form["image"].name}'
        )
