import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, User, Follow, Comment
from posts.settings import POST_NUM_ON_PAGE


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'auth'
FOLLOWER = 'follower'
NO_FOLLOWER = 'not-follower'
SLUG = 'test-slug'
NEW_SLUG = 'test-slug_new'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_posts', kwargs={'slug': SLUG})
NEW_GROUP_URL = reverse('posts:group_posts', kwargs={'slug': NEW_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME})
PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', kwargs={'username': USERNAME})
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower_user = User.objects.create_user(username=FOLLOWER)
        cls.no_follower = User.objects.create_user(username=NO_FOLLOWER)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PaginatorViewsTest.user)
        cls.follower = Client()
        cls.follower.force_login(PaginatorViewsTest.follower_user)
        cls.not_follower = Client()
        cls.not_follower.force_login(PaginatorViewsTest.no_follower)
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            pub_date='Тестовая дата',
            group=cls.group,
            image=cls.uploaded
        )
        cls.follow = Follow.objects.create(
            user=cls.follower_user,
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий к посту',
            pub_date='Тестовая дата'
        )
        cls.new_group = Group.objects.create(
            title='Новая группа',
            slug=NEW_SLUG,
            description='Тестовое описание новой группы',
        )
        cls.POST_DETAIL_PAGE = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.not_auth = Client()

    def test_pages_with_paginator(self):
        """На первой и на второй отображается корректное количество постов."""
        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'Тестовый текст {i + 1}',
                pub_date='Тестовая дата',
                group=self.group,
            ) for i in range(POST_NUM_ON_PAGE)
        )
        urls_names = [
            [INDEX_URL, POST_NUM_ON_PAGE],
            [GROUP_URL, POST_NUM_ON_PAGE],
            [PROFILE_URL, POST_NUM_ON_PAGE],
            [FOLLOW_URL, POST_NUM_ON_PAGE],
            [INDEX_URL + '?page=2', 1],
            [GROUP_URL + '?page=2', 1],
            [PROFILE_URL + '?page=2', 1],
            [FOLLOW_URL + '?page=2', 1]
        ]
        for urls_name, posts_number in urls_names:
            with self.subTest(urls_name=urls_name):
                response = self.follower.get(urls_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_number
                )

    def test_profile_with_author_show_correct_context(self):
        """Автор поста на странице пользователя."""
        response = self.authorized_client.get(PROFILE_URL)
        profile_author = response.context['author']
        self.assertEqual(profile_author, self.user)

    def test_pages_with_posts_show_correct_context(self):
        """
        Пост без искажений попал на страницу и
        группа в контексте групп-ленты без искажения атрибутов.
        """
        reverse_names = [
            INDEX_URL,
            GROUP_URL,
            PROFILE_URL,
            self.POST_DETAIL_PAGE,
            FOLLOW_URL
        ]
        for name in reverse_names:
            with self.subTest(name=name):
                response = self.follower.get(name)
                if name == self.POST_DETAIL_PAGE:
                    post = response.context['post']
                else:
                    posts = response.context['page_obj']
                    self.assertEqual(len(posts), 1)
                    post = posts[0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(
                    post.group.id,
                    self.post.group.id
                )
                self.assertEqual(
                    post.image,
                    self.post.image
                )

    def test_group_list_show_correct_context(self):
        """Группа появляется на странице групп-ленты без искажений атрибутов"""
        response = self.authorized_client.get(GROUP_URL)
        group = response.context['group']
        self.assertEqual(self.group.title, group.title)
        self.assertEqual(self.group.slug, group.slug)
        self.assertEqual(self.group.id, group.id)
        self.assertEqual(self.group.description, group.description)

    def test_post_is_not_on_another_group_list(self):
        """Посты с группой не отображается на странице другой группы"""
        response = self.authorized_client.get(NEW_GROUP_URL)
        self.assertNotIn(
            self.post,
            response.context['page_obj']
        )

    def test_cache_index_page(self):
        """На главной странице работает кэширование"""
        response_before = self.authorized_client.get(INDEX_URL)
        Post.objects.all().delete()
        response_after = self.authorized_client.get(INDEX_URL)
        self.assertEqual(
            response_before.content, response_after.content
        )
        cache.clear()
        response_clear_cache = self.authorized_client.get(INDEX_URL)
        self.assertNotEqual(
            response_after, response_clear_cache
        )

    def test_new_post_on_page_of_followers(self):
        """
        Новый пост появляется в лентах тех, кто подписан
        и не появляется в лентах других
        """
        Post.objects.all().delete()
        form_data = {
            'text': 'Пост создан для проверки',
            'group': self.group.id,
        }
        self.authorized_client.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        post_count_after = Post.objects.all().count()
        self.assertEqual(0, post_count_after - 1)
        new_post = Post.objects.get()
        self.follower.get(PROFILE_FOLLOW_URL)
        response = self.follower.get(FOLLOW_URL)
        self.assertIn(new_post, response.context['page_obj'])
        response = self.not_follower.get(FOLLOW_URL)
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_authorized_user_can_follow_author(self):
        """
        Авторизованный пользователь может
        подписаться на автора.
        """
        Follow.objects.all().delete()
        self.follower.get(PROFILE_FOLLOW_URL)
        follow_obj = Follow.objects.get()
        self.assertEqual(follow_obj.author, self.follow.author)
        self.assertEqual(follow_obj.user, self.follow.user)

    def test_authorized_user_can_unfollow_author(self):
        """
        Авторизованный пользователь может
        отписаться от автора.
        """
        self.follower.get(PROFILE_UNFOLLOW_URL)
        self.assertNotIn(self.follower, Follow.objects.all())

    def test_authorized_user_cannot_follow_yourself(self):
        """
        Авторизованный пользователь не может подписаться на самого себя.
        """
        follow_obj = Follow.objects.get()
        self.assertNotEqual(follow_obj.user, self.follow.author)
        Follow.objects.get().delete()
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        after_sibscribe = Follow.objects.all().count()
        self.assertEqual(after_sibscribe, 0)
