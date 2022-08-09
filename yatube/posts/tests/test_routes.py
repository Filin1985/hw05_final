from django.test import TestCase
from django.urls import reverse


POST_ID = 1
USERNAME = 'auth'
SLUG = 'test-slug'
URLS_NAMES = [
    ['posts:index', {}, '/'],
    ['posts:group_posts', {'slug': SLUG}, '/group/test-slug/'],
    ['posts:profile', {'username': USERNAME}, '/profile/auth/'],
    ['posts:post_create', {}, '/create/'],
    ['posts:post_detail', {'post_id': POST_ID}, f'/posts/{POST_ID}/'],
    ['posts:post_edit', {'post_id': POST_ID}, f'/posts/{POST_ID}/edit/'],
    ['posts:add_comment', {'post_id': POST_ID}, f'/posts/{POST_ID}/comment/'],
    ['posts:follow_index', {}, '/follow/'],
    ['posts:profile_follow', {'username': USERNAME},
        f'/profile/{USERNAME}/follow/'],
    [
        'posts:profile_unfollow',
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
                        name,
                        kwargs=constants
                    ),
                    url
                )
