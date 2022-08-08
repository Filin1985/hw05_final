import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, User, Follow, Comment
from posts.settings import POST_NUM_ON_PAGE


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'auth'
FOLLOWER = 'follower'
SLUG = 'test-slug'
NEW_SLUG = 'test-slug_new'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_posts', kwargs={'slug': SLUG})
NEW_GROUP_URL = reverse('posts:group_posts', kwargs={'slug': NEW_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
FOLLOW_URL = reverse('posts:follow_index')
PROF_FOLLOW_URL = reverse('posts:profile_follow',
                          kwargs={'username': USERNAME})
PROF_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', kwargs={'username': USERNAME})


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower_user = User.objects.create_user(username=FOLLOWER)
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
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
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        self.follower = Client()
        self.follower.force_login(PaginatorViewsTest.follower_user)

    def test_pages_with_paginator(self):
        """На первой и на второй отображается корректное количество постов."""
        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'Тестовый текст {i + 1}',
                pub_date='Тестовая дата',
                group=self.group,
            ) for i in range(POST_NUM_ON_PAGE + 1)
        )
        urls_names = [
            [INDEX_URL, POST_NUM_ON_PAGE],
            [GROUP_URL, POST_NUM_ON_PAGE],
            [PROFILE_URL, POST_NUM_ON_PAGE],
            [FOLLOW_URL, POST_NUM_ON_PAGE],
            [INDEX_URL + '?page=2', 2],
            [GROUP_URL + '?page=2', 2],
            [PROFILE_URL + '?page=2', 2],
            [FOLLOW_URL + '?page=2', 2]
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
            self.POST_DETAIL_PAGE
        ]
        for name in reverse_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
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
                self.assertEqual(
                    self.post.comments.values()[0]['text'],
                    post.comments.values()[0]['text']
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
        response = self.authorized_client.get(INDEX_URL)
        Post.objects.all().delete()
        self.assertContains(
            response, self.post.text, html=True
        )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower = User.objects.create_user(username=FOLLOWER)
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            pub_date='Тестовая дата',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowViewsTest.user)
        self.follower = Client()
        self.follower.force_login(FollowViewsTest.follower)

    def test_authorized_user_can_follow_author(self):
        """
        Авторизованный пользователь может
        подписаться и отписаться на автора.
        """
        before_sibscribe = Follow.objects.all().count()
        self.follower.get(PROF_FOLLOW_URL)
        after_sibscribe = Follow.objects.all().count()
        self.assertEqual(before_sibscribe, after_sibscribe - 1)
        self.follower.get(PROF_UNFOLLOW_URL)
        after_unsibscribe = Follow.objects.all().count()
        self.assertEqual(after_sibscribe, after_unsibscribe + 1)

    def test_authorized_user_cannot_follow_yourself(self):
        """
        Авторизованный пользователь не может подписаться на самого себя.
        """
        before_sibscribe = Follow.objects.all().count()
        self.authorized_client.get(PROF_FOLLOW_URL)
        after_sibscribe = Follow.objects.all().count()
        self.assertEqual(before_sibscribe, after_sibscribe)
