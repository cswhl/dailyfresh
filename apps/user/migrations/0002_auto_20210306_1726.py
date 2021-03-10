# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='is_default',
        ),
        migrations.AddField(
            model_name='address',
            name='is_defult',
            field=models.BooleanField(verbose_name='是否默认', default=False),
        ),
        migrations.AddField(
            model_name='address',
            name='test',
            field=models.BooleanField(verbose_name='默认', default=False),
        ),
    ]
