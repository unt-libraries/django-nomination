from datetime import datetime

import factory
from factory import fuzzy

from nomination import models


class ValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Value

    value = fuzzy.FuzzyText(length=20)
    key = fuzzy.FuzzyText(length=20)


class ValuesetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ValueSet

    name = fuzzy.FuzzyText(length=12)


class MetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Metadata

    name = fuzzy.FuzzyText(length=12)

    @factory.post_generation
    def value_sets(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for value_set in extracted:
                self.value_sets.add(value_set)


class MetadataValuesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Metadata_Values

    metadata = factory.SubFactory(MetadataFactory)
    value = factory.SubFactory(ValueFactory)
    value_order = fuzzy.FuzzyInteger(1)


class ValuesetValuesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Valueset_Values

    valueset = factory.SubFactory(ValuesetFactory)
    value = factory.SubFactory(ValueFactory)
    value_order = fuzzy.FuzzyInteger(1)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project

    project_name = fuzzy.FuzzyText(length=20)
    project_description = fuzzy.FuzzyText(length=20)
    project_slug = fuzzy.FuzzyText(length=20)
    project_start = fuzzy.FuzzyNaiveDateTime(datetime(2006, 1, 1))
    project_end = fuzzy.FuzzyNaiveDateTime(datetime.now(), datetime(2020, 1, 1))
    nomination_start = fuzzy.FuzzyNaiveDateTime(datetime(2006, 1, 1))
    nomination_end = fuzzy.FuzzyNaiveDateTime(datetime.now(), datetime(2020, 1, 1))
    admin_name = fuzzy.FuzzyText(length=12)
    admin_email = factory.LazyAttribute(lambda x: '{0}@email.com'.format(x.admin_name))
    project_url = factory.LazyAttribute(lambda x: 'http://{0}.com'.format(x.project_slug))
    registration_required = fuzzy.FuzzyChoice([True, False])


class ProjectMetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project_Metadata

    project = factory.SubFactory(ProjectFactory)
    metadata = factory.SubFactory(MetadataFactory)
    required = False
    form_type = fuzzy.FuzzyChoice([
        'checkbox',
        'date',
        'radio',
        'select',
        'selectsingle',
        'text',
        'textarea'])
    description = 'Test metadata'
    metadata_order = fuzzy.FuzzyInteger(1)
    help = fuzzy.FuzzyText(length=20)


class NominatorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Nominator

    nominator_name = fuzzy.FuzzyText(length=12)
    nominator_institution = fuzzy.FuzzyText(length=20)
    nominator_email = factory.LazyAttribute(lambda x: '{0}@email.com'.format(x.nominator_name))


class URLFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.URL

    url_project = factory.SubFactory(ProjectFactory)
    url_nominator = factory.SubFactory(NominatorFactory)
    entity = fuzzy.FuzzyText(length=8, prefix='http://www.', suffix='.net')
    attribute = fuzzy.FuzzyText(length=20)
    value = fuzzy.FuzzyText(length=10)


class NominatedURLFactory(URLFactory):
    attribute = 'nomination'
    value = fuzzy.FuzzyChoice(['-1', '1'])


class SURTFactory(URLFactory):
    attribute = 'surt'
    value = fuzzy.FuzzyText(length=5, prefix='http://(com,', suffix=',www,)')
