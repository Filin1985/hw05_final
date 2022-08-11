from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from posts.models import Post, Group, User


USERNAME = 'auth'
NOTAUTHOR = 'not-auth'
SLUG = 'test-slug'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_posts', kwargs={'slug': SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME})
PROFILE_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', kwargs={'username': USERNAME})
LOGIN_URL = reverse('users:login')
UNEXISTING_URL = '/unexisting_page/'
CREATE_REDIRECT = f'{LOGIN_URL}?next={CREATE_URL}'
FOLLOW_REDIRECT = f'{LOGIN_URL}?next={FOLLOW_URL}'
PROFILE_FOLLOW_REDIRECT = f'{LOGIN_URL}?next={PROFILE_FOLLOW_URL}'
PROFILE_UNFOLLOW_REDIRECT = f'{LOGIN_URL}?next={PROFILE_UNFOLLOW_URL}'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.not_author = User.objects.create_user(username=NOTAUTHOR)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.authorized = Client()
        cls.authorized.force_login(cls.not_author)
        cls.guest = Client()
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
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.EDIT_REDIRECT = f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'

    def test_unathorized_url_exists_at_desired_location(self):
        """Проверка доступности urls адресов"""
        urls_cases = [
            [INDEX_URL, self.guest, HTTPStatus.OK],
            [GROUP_URL, self.guest, HTTPStatus.OK],
            [PROFILE_URL, self.authorized, HTTPStatus.OK],
            [CREATE_URL, self.author, HTTPStatus.OK],
            [CREATE_URL, self.guest, HTTPStatus.FOUND],
            [FOLLOW_URL, self.author, HTTPStatus.OK],
            [FOLLOW_URL, self.guest, HTTPStatus.FOUND],
            [PROFILE_FOLLOW_URL, self.authorized, HTTPStatus.FOUND],
            [PROFILE_FOLLOW_URL, self.author, HTTPStatus.FOUND],
            [PROFILE_FOLLOW_URL, self.guest, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.authorized, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.guest, HTTPStatus.FOUND],
            [PROFILE_UNFOLLOW_URL, self.author, HTTPStatus.FOUND],
            [UNEXISTING_URL, self.guest, HTTPStatus.NOT_FOUND],
            [self.POST_DETAIL_URL, self.guest, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.author, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.guest, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.authorized, HTTPStatus.FOUND],
        ]
        for url, client, status in urls_cases:
            with self.subTest(url=url, client=client, status=status):
                self.assertEqual(
                    client.get(url).status_code,
                    status,
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = [
            [INDEX_URL, self.author, 'posts/index.html'],
            [GROUP_URL, self.author, 'posts/group_list.html'],
            [PROFILE_URL, self.author, 'posts/profile.html'],
            [self.POST_DETAIL_URL, self.author, 'posts/post_detail.html'],
            [CREATE_URL, self.author, 'posts/create_post.html'],
            [self.POST_EDIT_URL, self.author, 'posts/create_post.html'],
            [FOLLOW_URL, self.author, 'posts/follow.html'],
            [UNEXISTING_URL, self.author, 'core/404.html']
        ]
        for address, client, template in templates_url_names:
            with self.subTest(address=address):
                self.assertTemplateUsed(client.get(address), template)

    def test_posts_list_url_redirect(self):
        """
        Страницы создания поста и редактирования
        поста перенаправят анонимного пользователя
        на страницу логина.
        """
        cases = [
            [CREATE_REDIRECT, CREATE_URL, self.guest],
            [FOLLOW_REDIRECT, FOLLOW_URL, self.guest],
            [PROFILE_UNFOLLOW_REDIRECT, PROFILE_UNFOLLOW_URL, self.guest],
            [PROFILE_FOLLOW_REDIRECT, PROFILE_FOLLOW_URL, self.guest],
            [self.EDIT_REDIRECT, self.POST_EDIT_URL, self.guest],
            [self.POST_DETAIL_URL, self.POST_EDIT_URL, self.authorized],
            [PROFILE_URL, PROFILE_FOLLOW_URL, self.authorized],
            [PROFILE_URL, PROFILE_UNFOLLOW_URL, self.authorized],
            [PROFILE_URL, PROFILE_FOLLOW_URL, self.author],
            [PROFILE_URL, PROFILE_UNFOLLOW_URL, self.author],
        ]
        for destination, url, user in cases:
            with self.subTest(destination=destination, url=url, user=user):
                self.assertRedirects(
                    user.get(url),
                    destination
                )
