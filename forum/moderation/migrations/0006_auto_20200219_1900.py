# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-02-19 18:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0005_auto_20200101_1806'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='moderatorevent',
            options={'verbose_name': 'Moderator Event'},
        ),
    ]
