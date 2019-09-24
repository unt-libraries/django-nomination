from datetime import datetime, timedelta

from django.conf import settings

import pytest

from . import factories


pytestmark = pytest.mark.django_db


class TestValue:
    def test_unicode(self):
        value = factories.ValueFactory.build()
        assert str(value) == value.value


class TestValueSet:
    def test_unicode(self):
        valueset = factories.ValuesetFactory.build()
        assert str(valueset) == valueset.name


class TestMetadata:
    def test_unicode(self):
        metadata = factories.MetadataFactory.create()
        assert str(metadata) == metadata.name


class TestMetadataValues:
    def test_unicode(self):
        metadata_values = factories.MetadataValuesFactory.create()
        assert str(metadata_values) == '{0} ({1})'.format(
            metadata_values.metadata, metadata_values.value)


class TestValuesetValues:
    def test_unicode(self):
        valueset_values = factories.ValuesetValuesFactory.create()
        assert str(valueset_values) == '{0} ({1})'.format(
            valueset_values.valueset, valueset_values.value)


class TestProject:
    def test_unicode(self):
        project = factories.ProjectFactory.build()
        assert str(project) == project.project_slug

    def test_nomination_message_before_nomination_window(self):
        project = factories.ProjectFactory.build(
            nomination_start=datetime.now() + timedelta(days=1),
            nomination_end=datetime.now() + timedelta(days=5)
        )

        assert project.nomination_message() == (
            'Nomination for this project starts on {0}'
            .format(project.nomination_start.strftime('%b %d, %Y'))
        )

    def test_nomination_message_during_nomination_window(self):
        project = factories.ProjectFactory.build(
            nomination_start=datetime.now() - timedelta(days=1),
            nomination_end=datetime.now() + timedelta(days=5)
        )

        assert project.nomination_message() is None

    def test_nomination_message_after_nomination_window(self):
        project = factories.ProjectFactory.build(
            nomination_start=datetime.now() - timedelta(days=5),
            nomination_end=datetime.now() - timedelta(days=1)
        )

        assert project.nomination_message() == (
            'Nomination for this project ended on {0}'
            .format(project.nomination_end.strftime('%b %d, %Y'))
        )

    def test_project_active_when_project_active(self):
        project = factories.ProjectFactory.build(
            project_start=datetime.now() - timedelta(days=1),
            project_end=datetime.now() + timedelta(days=5)
        )

        assert project.project_active() is True

    def test_project_active_when_project_inactive(self):
        project = factories.ProjectFactory.build(
            project_start=datetime.now() + timedelta(days=1),
            project_end=datetime.now() + timedelta(days=5)
        )

        assert project.project_active() is False

    def test_nomination_active_when_nomination_active(self):
        project = factories.ProjectFactory.build(
            nomination_start=datetime.now() - timedelta(days=1),
            nomination_end=datetime.now() + timedelta(days=5)
        )

        assert project.nomination_active() is True

    def test_nomination_active_when_nomination_inactive(self):
        project = factories.ProjectFactory.build(
            nomination_start=datetime.now() + timedelta(days=1),
            nomination_end=datetime.now() + timedelta(days=5)
        )

        assert project.nomination_active() is False

    @pytest.mark.parametrize('archive_url', [
        None,
        ''
    ])
    def test_archive_url_with_no_url(self, archive_url):
        project = factories.ProjectFactory.build(
            archive_url=archive_url
        )
        project.clean()
        assert project.archive_url is archive_url

    @pytest.mark.parametrize('archive_url', [
        'http://www.example.com',
        'http://www.example.com/'
    ])
    def test_archive_url(self, archive_url):
        project = factories.ProjectFactory.build(
            archive_url=archive_url
        )
        project.clean()

        assert project.archive_url == 'http://www.example.com/'


class TestProjectMetadata:
    def test_unicode(self):
        project_metadata = factories.ProjectMetadataFactory.create()
        assert str(project_metadata) == '{0} ({1})'.format(
            project_metadata.project, project_metadata.metadata)


class TestNominator:
    def test_unicode(self):
        nominator = factories.NominatorFactory.build()
        assert str(nominator) == nominator.nominator_name

    def test_nominations(self):
        num_nominations = 10
        nominator = factories.NominatorFactory.create()
        factories.NominatedURLFactory.create_batch(10, url_nominator=nominator)
        assert nominator.nominations() == num_nominations


class TestURL:
    entity_display_html = (
        "<a href='http://example.com/admin/nomination/url/{0}'>{1}</a>&nbsp;"
        "<a href='{1}'><img src='{2}nomination/images/external-link.gif'/></a>"
    )
    project_link_html = "<a href='http://example.com/admin/nomination/project/{0}'>{1}</a>"
    nominator_link_html = "<a href='http://example.com/admin/nomination/nominator/{0}'>{1}</a>"

    def test_unicode(self):
        url = factories.URLFactory.create()
        assert str(url) == url.entity

    def test_entity_display(self):
        url = factories.URLFactory.create()
        assert url.entity_display() == self.entity_display_html.format(
            url.id, url.entity, settings.STATIC_URL)

    def test_get_project(self):
        url = factories.URLFactory.create()
        assert url.get_project() == self.project_link_html.format(
            url.url_project.id, url.url_project)

    def test_get_nominator(self):
        url = factories.URLFactory.create()
        assert url.get_nominator() == self.nominator_link_html.format(
            url.url_nominator.id, url.url_nominator)
