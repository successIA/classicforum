# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-02-27 02:01
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='views',
        ),
    ]
