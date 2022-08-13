from django.test import Client, TestCase

from posts.models import Post, Group, User, Comment, Follow


USERNAME = 'auth'
FOLLOWER = 'follower'
# FOLLOW_STR = '{user} подписан на {author}'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower_user = User.objects.create_user(username=FOLLOWER)
        cls.follower = Client()
        cls.follower.force_login(PostModelTest.follower_user)
        cls.group = Group.objects.create(
            title='Имя группы',
            slug='Идентификатор',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для проверки вывода длинной строки',
            pub_date='Дата публикации',
            group=cls.group,
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
        cls.FOLLOW_STR = cls.follow.__str__()

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает str."""
        self.assertEqual(str(self.post), self.post.text[:15])
        self.assertEqual(str(self.group), self.group.title)
        self.assertEqual(str(self.comment), self.comment.text[:15])
        self.assertEqual(
            str(self.follow),
            self.FOLLOW_STR.format(
                user=self.follow.user.username,
                author=self.follow.author.username
            )
        )

    def test_verbose_name_post(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_post(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_verbose_name_comment(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Комментарий',
            'pub_date': 'Дата комментария',
            'author': 'Автор',
            'post': 'Пост',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_comment(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите свой комментарий',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).help_text,
                    expected_value
                )
