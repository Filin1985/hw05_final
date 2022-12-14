# Generated by Django 2.2.16 on 2022-08-08 12:53

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_remove_post_image'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='уникальная подписка'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(user=django.db.models.expressions.F('author')), name='подписка на самого себя'),
        ),
    ]
