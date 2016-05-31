# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomination', '0002_auto_20160406_2138'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='archive_url',
            field=models.URLField(help_text=b'Base URL for accessing site archives.', null=True, blank=True),
        ),
    ]
