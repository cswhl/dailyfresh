# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20210306_1726'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='is_defult',
            new_name='is_default',
        ),
    ]
