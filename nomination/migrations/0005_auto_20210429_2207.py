# Generated by Django 2.2.20 on 2021-04-29 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomination', '0004_auto_20190927_1904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nominator',
            name='nominator_email',
            field=models.CharField(help_text='An email address for identifying your nominations in the system.', max_length=100, unique=True),
        ),
    ]
