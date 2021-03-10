# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_remove_address_test'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='receiber',
            new_name='receiver',
        ),
    ]
