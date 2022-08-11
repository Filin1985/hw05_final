from django.test import TestCase
from django.urls import reverse
from ..urls import app_name


POST_ID = 1
USERNAME = 'auth'
SLUG = 'test-slug'
URLS_NAMES = [
    ['index', {}, '/'],
    ['group_posts', {'slug': SLUG}, '/group/test-slug/'],
    ['profile', {'username': USERNAME}, '/profile/auth/'],
    ['post_create', {}, '/create/'],
    ['post_detail', {'post_id': POST_ID}, f'/posts/{POST_ID}/'],
    ['post_edit', {'post_id': POST_ID}, f'/posts/{POST_ID}/edit/'],
    ['add_comment', {'post_id': POST_ID}, f'/posts/{POST_ID}/comment/'],
    ['follow_index', {}, '/follow/'],
    ['profile_follow', {'username': USERNAME},
        f'/profile/{USERNAME}/follow/'],
    [
        'profile_unfollow',
        {'username': USERNAME},
        f'/profile/{USERNAME}/unfollow/'
    ],
]


class PostURLTests(TestCase):
    def test_routes_string_for_each_url_name(self):
        """Вызов маршрутов возвращает ожидаемые urls"""
        for name, constants, url in URLS_NAMES:
            with self.subTest(name=name):
                self.assertEqual(
                    reverse(
                        f'{app_name}:{name}',
                        kwargs=constants
                    ),
                    url
                )
