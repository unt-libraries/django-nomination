# -*- coding: utf-8 -*-


from django.db import models, migrations


def add_system_nominator(apps, schema_editor):
    Nominator = apps.get_model('nomination', 'Nominator')
    system_nominator = Nominator(
        id=1,
        nominator_email='system',
        nominator_name='Nomination Tool System',
        nominator_institution='Nomination Tool System'
    )
    system_nominator.save()


class Migration(migrations.Migration):

    dependencies = [
        ('nomination', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_system_nominator),
    ]
