# Generated by Django 2.2.16 on 2022-08-08 13:53

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20220808_1553'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='подписка на самого себя',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(user=django.db.models.expressions.F('user')), name='подписка на самого себя'),
        ),
    ]
