from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        templates_public_urls = {
            HTTPStatus.OK: '/auth/logout/',
            HTTPStatus.OK: '/auth/signup/',
            HTTPStatus.OK: '/auth/login/',
            HTTPStatus.OK: '/auth/password_change/',
            HTTPStatus.OK: '/auth/password_change/done/',
            HTTPStatus.OK: '/auth/password_reset/',
            HTTPStatus.OK: '/auth/password_reset/done/',
            HTTPStatus.OK: '/auth/reset/1/2/',
            HTTPStatus.OK: '/auth/reset/done/',
        }
        for status, address in templates_public_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                print(response)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'users/logged_out.html': '/auth/logout/',
            'users/signup.html': '/auth/signup/',
            'users/login.html': '/auth/login/',
            'users/password_reset_form.html':
                '/auth/password_reset/',
            'users/password_reset_done.html':
                '/auth/password_reset/done/',
            'users/password_reset_confirm.html':
                '/auth/reset/Mw/5si-f7ab5e9f2a875e9b7c61/',
            'users/password_reset_complete.html':
                '/auth/reset/done/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
