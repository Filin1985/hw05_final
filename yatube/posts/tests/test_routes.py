from django.test import TestCase
from django.urls import reverse


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
    ['follow_index', {}, f'/follow/'],
    ['profile_follow', {'username': USERNAME}, f'/profile/auth/follow/'],
    ['profile_unfollow', {'username': USERNAME}, f'/profile/auth/unfollow/'],
]


class PostURLTests(TestCase):
    def test_routes_string_for_each_url_name(self):
        """Вызов маршрутов возвращает ожидаемые urls"""
        for name, constant, url in URLS_NAMES:
            with self.subTest(name=name):
                self.assertEqual(
                    reverse(
                        f'posts:{name}',
                        kwargs=constant
                    ),
                    url
                )
