import datetime
from django.db import models
from django.contrib.sites.models import Site
from django.conf import settings

FORM_TYPES = (
    ('checkbox', 'checkbox'),
    ('date', 'date'),
    ('radio', 'radio button'),
    ('select', 'menu-select multiple values'),
    ('selectsingle', 'menu-select single value'),
    ('text', 'text input'),
    ('textarea', 'text area'),
)


class Value(models.Model):
    # metadata = models.ForeignKey(Metadata)
    value = models.CharField(max_length=255,
                             help_text='Permitted value for associated metadata field.')
    key = models.CharField(max_length=35,
                           help_text='Up to 35 character identifier for the metadata field.',
                           unique=True)

    class Meta:
        # unique_together = (('key', 'metadata'),)
        ordering = ['value']
        verbose_name = 'metadata value'
        verbose_name_plural = 'metadata values'

    def __unicode__(self):
        return self.value


class ValueSet(models.Model):
    """Reusable sets of metadata values."""
    name = models.CharField(max_length=75, unique=True, help_text='Name given to value set.')
    values = models.ManyToManyField(Value, through='Valueset_Values', verbose_name='values')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'metadata value set'
        verbose_name_plural = 'metadata value sets'


class Metadata(models.Model):
    # project = models.ForeignKey(Project)
    name = models.SlugField(
        max_length=50,
        help_text=(
            'Assign a name for the metadata field (letters, numbers, '
            'underscores, and hyphens are permissible).'
        )
    )
    # required = models.BooleanField(
    #     help_text='Are users required to submit data for this field when nominating a URL?'
    # )
    values = models.ManyToManyField(
        Value,
        through='Metadata_Values',
        blank=True,
        help_text='Allowed value for metadata field.',
        verbose_name='values'
    )
    value_sets = models.ManyToManyField(
        ValueSet,
        blank=True,
        help_text=('In addition to values manually assigned, values in selected pre-defined sets '
                   'will also be available to metadata fields.'),
        verbose_name='metadata value sets'
    )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'metadata field'
        verbose_name_plural = 'metadata fields'
        ordering = ['name']


class Metadata_Values(models.Model):
    metadata = models.ForeignKey(Metadata)
    value = models.ForeignKey(Value)
    value_order = models.PositiveIntegerField(
        default=1,
        help_text='Change the ordering of the value fields, ordered lowest to highest'
    )

    def __unicode__(self):
        return u'%s (%s)' % (self.metadata, self.value)

    class Meta:
        verbose_name = 'metadata values'
        verbose_name_plural = 'metadata values'
        ordering = ['value_order']


class Valueset_Values(models.Model):
    valueset = models.ForeignKey(ValueSet)
    value = models.ForeignKey(Value)
    value_order = models.PositiveIntegerField(
        default=1,
        help_text='Change the ordering of the value fields, ordered lowest to highest'
    )

    def __unicode__(self):
        return u'%s (%s)' % (self.valueset, self.value)

    class Meta:
        verbose_name = 'valueset values'
        verbose_name_plural = 'valueset values'
        ordering = ['value_order', 'value']


class Project(models.Model):
    project_name = models.CharField(max_length=250, help_text='Name given to nomination project.')
    project_description = models.TextField(help_text='Description of project.')
    project_slug = models.CharField(
        max_length=25,
        unique=True,
        help_text='Up to 25 character identifier for the project (used in URLS, etc.).',
        )
    project_start = models.DateTimeField(help_text='Starting date for project.')
    project_end = models.DateTimeField(help_text='Ending date for project.')
    nomination_start = models.DateTimeField(help_text='Date to start accepting URL nominations.')
    nomination_end = models.DateTimeField(help_text='Date to stop accepting URL nominations.')
    admin_name = models.CharField(max_length=80, help_text='Name of project administrator.')
    admin_email = models.CharField(max_length=80,
                                   help_text='Email address of project administrator.')
    project_url = models.CharField(max_length=255, help_text='Project affiliated URL.')
    archive_url = models.URLField(help_text='Base URL for accessing site archives.', null=True,
                                  blank=True)
    registration_required = models.BooleanField()
    metadata = models.ManyToManyField(Metadata, through='Project_Metadata')

    def __unicode__(self):
        return self.project_slug

    def nomination_message(self):
        if datetime.datetime.now() < self.nomination_start:
            return 'Nomination for this project starts on ' + \
                str(self.nomination_start.strftime("%b %d, %Y"))
        elif self.nomination_end < datetime.datetime.now():
            return 'Nomination for this project ended on ' + \
                str(self.nomination_end.strftime("%b %d, %Y"))
        else:
            return None

    def project_active(self):
        if datetime.datetime.now() > self.project_start and \
                datetime.datetime.now() < self.project_end:
            return True
        else:
            return False

    def nomination_active(self):
        if datetime.datetime.now() > self.nomination_start and \
                datetime.datetime.now() < self.nomination_end:
            return True
        else:
            return False

    def clean(self):
        if self.archive_url and not self.archive_url.endswith('/'):
            self.archive_url = '{0}{1}'.format(self.archive_url, '/')


class Project_Metadata(models.Model):
    project = models.ForeignKey(Project)
    metadata = models.ForeignKey(Metadata)
    required = models.BooleanField(
        help_text='Are users required to submit data for this field when nominating a URL?'
    )
    form_type = models.CharField(
        max_length=30,
        choices=FORM_TYPES,
        help_text='Type of HTML form element that should represent the field.'
    )
    help = models.CharField(
        max_length=255,
        blank=True,
        help_text='String used on Web forms to prompt users for accurate data.'
    )
    description = models.CharField(
        max_length=255,
        help_text='Used as a descriptive title for the metadata field on Web forms.'
    )
    metadata_order = models.PositiveIntegerField(
        default=1,
        help_text='Change the ordering of the metadata fields, ordered lowest to highest'
    )

    def __unicode__(self):
        return u'%s (%s)' % (self.project, self.metadata)

    class Meta:
        ordering = ['metadata_order']
        verbose_name_plural = 'project metadata'


class Nominator(models.Model):
    nominator_name = models.CharField(max_length=100, help_text='Your name.')
    nominator_institution = models.CharField(
        max_length=100,
        help_text='Your institutional affiliation.'
    )
    nominator_email = models.CharField(
        max_length=100,
        help_text='An email address for identifying your nominations in the system.'
    )

    def __unicode__(self):
        return self.nominator_name

    class Meta:
        ordering = ['nominator_name']

    def nominations(self):
        return len(URL.objects.filter(url_nominator=self.id))


class URL(models.Model):
    url_project = models.ForeignKey(Project,
                                    help_text='The project for which you want to add a URL.')
    url_nominator = models.ForeignKey(Nominator)
    entity = models.CharField(max_length=300, help_text='The URL to nominate for capture.')
    attribute = models.CharField(max_length=255,
                                 help_text='A property of the URL you wish to describe.')
    value = models.CharField(max_length=255, help_text='The value of the associated attribute.')
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.entity

    def entity_display(self):
        return(
            "<a href=\'http://%s/admin/nomination/url/%s\'>%s</a>&nbsp;"
            "<a href=\'%s\'><img src=\'%snomination/images/external-link.gif\'/></a>"
            % (Site.objects.get_current().domain, self.id, self.entity, self.entity,
               settings.STATIC_URL)
        )
    entity_display.short_description = 'Entity'
    entity_display.allow_tags = True

    def get_project(self):
        return "<a href=\'http://%s/admin/nomination/project/%s\'>%s</a>" % \
                    (Site.objects.get_current().domain, self.url_project.id, self.url_project)
    get_project.short_description = 'Project'
    get_project.allow_tags = True

    def get_nominator(self):
        return "<a href=\'http://%s/admin/nomination/nominator/%s\'>%s</a>" % \
                    (Site.objects.get_current().domain, self.url_nominator.id, self.url_nominator)
    get_nominator.short_description = 'Nominator'
    get_nominator.allow_tags = True
