# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(help_text=b'Assign a name for the metadata field (letters, numbers, underscores, and hyphens are permissible).')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'metadata field',
                'verbose_name_plural': 'metadata fields',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Metadata_Values',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_order', models.PositiveIntegerField(default=1, help_text=b'Change the ordering of the value fields, ordered lowest to highest')),
                ('metadata', models.ForeignKey(to='nomination.Metadata', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['value_order'],
                'verbose_name': 'metadata values',
                'verbose_name_plural': 'metadata values',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Nominator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nominator_name', models.CharField(help_text=b'Your name.', max_length=100)),
                ('nominator_institution', models.CharField(help_text=b'Your institutional affiliation.', max_length=100)),
                ('nominator_email', models.CharField(help_text=b'An email address for identifying your nominations in the system.', max_length=100)),
            ],
            options={
                'ordering': ['nominator_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('project_name', models.CharField(help_text=b'Name given to nomination project.', max_length=250)),
                ('project_description', models.TextField(help_text=b'Description of project.')),
                ('project_slug', models.CharField(help_text=b'Up to 25 character identifier for the project (used in URLS, etc.).', unique=True, max_length=25)),
                ('project_start', models.DateTimeField(help_text=b'Starting date for project.')),
                ('project_end', models.DateTimeField(help_text=b'Ending date for project.')),
                ('nomination_start', models.DateTimeField(help_text=b'Date to start accepting URL nominations.')),
                ('nomination_end', models.DateTimeField(help_text=b'Date to stop accepting URL nominations.')),
                ('admin_name', models.CharField(help_text=b'Name of project administrator.', max_length=80)),
                ('admin_email', models.CharField(help_text=b'Email address of project administrator.', max_length=80)),
                ('project_url', models.CharField(help_text=b'Project affiliated URL.', max_length=255)),
                ('registration_required', models.BooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project_Metadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('required', models.BooleanField(help_text=b'Are users required to submit data for this field when nominating a URL?')),
                ('form_type', models.CharField(help_text=b'Type of HTML form element that should represent the field.', max_length=30, choices=[(b'checkbox', b'checkbox'), (b'date', b'date'), (b'radio', b'radio button'), (b'select', b'menu-select multiple values'), (b'selectsingle', b'menu-select single value'), (b'text', b'text input'), (b'textarea', b'text area')])),
                ('help', models.CharField(help_text=b'String used on Web forms to prompt users for accurate data.', max_length=255, blank=True)),
                ('description', models.CharField(help_text=b'Used as a descriptive title for the metadata field on Web forms.', max_length=255)),
                ('metadata_order', models.PositiveIntegerField(default=1, help_text=b'Change the ordering of the metadata fields, ordered lowest to highest')),
                ('metadata', models.ForeignKey(to='nomination.Metadata', on_delete=models.CASCADE)),
                ('project', models.ForeignKey(to='nomination.Project', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['metadata_order'],
                'verbose_name_plural': 'project metadata',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='URL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entity', models.CharField(help_text=b'The URL to nominate for capture.', max_length=300)),
                ('attribute', models.CharField(help_text=b'A property of the URL you wish to describe.', max_length=255)),
                ('value', models.CharField(help_text=b'The value of the associated attribute.', max_length=255)),
                ('date', models.DateTimeField(auto_now=True)),
                ('url_nominator', models.ForeignKey(to='nomination.Nominator', on_delete=models.CASCADE)),
                ('url_project', models.ForeignKey(help_text=b'The project for which you want to add a URL.', to='nomination.Project', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(help_text=b'Permitted value for associated metadata field.', max_length=255)),
                ('key', models.CharField(help_text=b'Up to 35 character identifier for the metadata field.', unique=True, max_length=35)),
            ],
            options={
                'ordering': ['value'],
                'verbose_name': 'metadata value',
                'verbose_name_plural': 'metadata values',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValueSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Name given to value set.', unique=True, max_length=75)),
            ],
            options={
                'verbose_name': 'metadata value set',
                'verbose_name_plural': 'metadata value sets',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Valueset_Values',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_order', models.PositiveIntegerField(default=1, help_text=b'Change the ordering of the value fields, ordered lowest to highest')),
                ('value', models.ForeignKey(to='nomination.Value', on_delete=models.CASCADE)),
                ('valueset', models.ForeignKey(to='nomination.ValueSet', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['value_order', 'value'],
                'verbose_name': 'valueset values',
                'verbose_name_plural': 'valueset values',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='valueset',
            name='values',
            field=models.ManyToManyField(to='nomination.Value', verbose_name=b'values', through='nomination.Valueset_Values'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='metadata',
            field=models.ManyToManyField(to='nomination.Metadata', through='nomination.Project_Metadata'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata_values',
            name='value',
            field=models.ForeignKey(to='nomination.Value', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='value_sets',
            field=models.ManyToManyField(help_text=b'In addition to values manually assigned, values in selected pre-defined sets will also be available to metadata fields.', to='nomination.ValueSet', verbose_name=b'metadata value sets', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='values',
            field=models.ManyToManyField(help_text=b'Allowed value for metadata field.', to='nomination.Value', verbose_name=b'values', through='nomination.Metadata_Values', blank=True),
            preserve_default=True,
        ),
    ]
