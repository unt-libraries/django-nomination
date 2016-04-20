import pytest
from datetime import timedelta

from django.http import Http404

from nomination import feeds
from . import factories


pytestmark = pytest.mark.django_db


class TestURLFeed:

    def test_get_object(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        feed = feeds.url_feed()
        obj = feed.get_object(request, project.project_slug)

        assert obj == project

    def test_get_object_raises_404(self, rf):
        request = rf.get('/')
        feed = feeds.url_feed()

        with pytest.raises(Http404):
            feed.get_object(request, '')

    def test_title(self):
        project = factories.ProjectFactory(project_name='Test Project')
        feed = feeds.url_feed()
        title = feed.title(project)

        assert title == 'Latest URLs for Test Project'

    def test_link(self, rf):
        project = factories.ProjectFactory(project_slug='test_project')
        request = rf.get('/')
        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        link = feed.link(project)

        assert link == '/nomination/test_project/feed/urls/'

    def test_subtitle(self):
        project = factories.ProjectFactory(project_name='Test Project')
        feed = feeds.url_feed()
        subtitle = feed.subtitle(project)

        assert subtitle == 'RSS feed for the most recent URLs added to Test Project.'

    def test_items_returns_only_project_surts(self):
        project = factories.ProjectFactory()
        surts = factories.SURTFactory.create_batch(3, url_project=project)
        factories.URLFactory.create_batch(3, url_project=project)
        factories.SURTFactory.create_batch(3)

        feed = feeds.url_feed()
        items = feed.items(project)

        assert len(items) == 3
        for surt in items:
            assert surt in surts

    def test_items_returns_sorted_surts(self):
        """Items returned should be sorted by item.date"""
        project = factories.ProjectFactory()
        surts = factories.SURTFactory.create_batch(2, url_project=project)
        # Adjust dates to reverse the sorted order of the SURTs.
        surts[1].date -= timedelta(days=3)

        feed = feeds.url_feed()
        items = feed.items(project)

        assert items[0] == surts[1]
        assert items[1] == surts[0]

    def test_item_link(self, rf):
        project = factories.ProjectFactory(project_slug='test_project')
        surt = factories.SURTFactory(url_project=project, entity='http://www.example.com')
        request = rf.get('/')

        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        item_link = feed.item_link(surt)

        assert item_link == '/nomination/test_project/url/http://www.example.com/'

    def test_item_pubdate(self):
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        feed = feeds.url_feed()
        item_pubdate = feed.item_pubdate(surt)

        assert item_pubdate == surt.date

    def test_item_title(self, rf):
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        url = factories.URLFactory(url_project=project, entity=surt.entity, attribute='Site_Name')
        request = rf.get('/')

        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        item_title = feed.item_title(surt)

        assert item_title == url.value

    def test_item_title_returns_url_title(self, rf):
        """If the URL has no site name on record, return the title."""
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        url = factories.URLFactory(url_project=project, entity=surt.entity, attribute='Title')
        request = rf.get('/')

        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        item_title = feed.item_title(surt)

        assert item_title == url.value

    def test_item_title_returns_entity(self, rf):
        """If the URL has no site name or title on record, return the URL."""
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        request = rf.get('/')

        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        item_title = feed.item_title(surt)

        assert item_title == surt.entity

    def test_item_description(self, rf):
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project, entity='www.example.com')
        factories.URLFactory(
            url_project=project,
            entity=surt.entity,
            attribute='Description',
            value='Home Page'
        )
        request = rf.get('/')

        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        item_description = feed.item_description(surt)

        assert item_description == 'www.example.com - Home Page'

    def test_item_description_returns_entity(self, rf):
        """If the URL has no description, return just the URL itself."""
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        request = rf.get('/')

        feed = feeds.url_feed()
        feed.get_object(request, project.project_slug)
        item_description = feed.item_description(surt)

        assert item_description == surt.entity


class TestNominationFeed:

    def test_get_object(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        feed = feeds.nomination_feed()
        obj = feed.get_object(request, project.project_slug)

        assert obj == project

    def test_get_object_raises_404(self, rf):
        request = rf.get('/')
        feed = feeds.nomination_feed()
        with pytest.raises(Http404):
            feed.get_object(request, '')

    def test_title(self):
        project = factories.ProjectFactory(project_name='Test Project')
        feed = feeds.nomination_feed()
        title = feed.title(project)

        assert title == 'Most Recent Nominations for Test Project'

    def test_link(self, rf):
        project = factories.ProjectFactory(project_slug='test_project')
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        link = feed.link(project)

        assert link == '/nomination/test_project/feed/nominations/'

    def test_subtitle(self):
        project = factories.ProjectFactory(project_name='Test Project')
        feed = feeds.nomination_feed()
        subtitle = feed.subtitle(project)

        assert subtitle == ('RSS feed for the most recently nominated URLs for Test Project. '
                            'Includes newly added URLs and subsequent nominations of '
                            'those URLs.')

    def test_items_returns_only_project_nominations(self):
        project = factories.ProjectFactory()
        noms = factories.NominatedURLFactory.create_batch(3, url_project=project)
        factories.URLFactory.create_batch(3, url_project=project)
        factories.NominatedURLFactory.create_batch(3)

        feed = feeds.nomination_feed()
        items = feed.items(project)

        assert len(items) == 3
        for nom in items:
            assert nom in noms

    def test_items_returns_sorted_nominations(self):
        """Items returned should be sorted by item.date"""
        project = factories.ProjectFactory()
        noms = factories.NominatedURLFactory.create_batch(2, url_project=project)
        # Adjust dates to reverse the sorted order of the nominations.
        noms[1].date -= timedelta(days=3)

        feed = feeds.nomination_feed()
        items = feed.items(project)

        assert items[0] == noms[1]
        assert items[1] == noms[0]

    def test_item_link(self, rf):
        project = factories.ProjectFactory(project_slug='test_project')
        nom = factories.NominatedURLFactory(url_project=project, entity='http://www.example.com')
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        item_link = feed.item_link(nom)

        assert item_link == '/nomination/test_project/url/http://www.example.com/'

    def test_item_pubdate(self):
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        feed = feeds.nomination_feed()
        item_pubdate = feed.item_pubdate(nom)

        assert item_pubdate == nom.date

    def test_item_title(self, rf):
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        url = factories.URLFactory(url_project=project, entity=nom.entity, attribute='Site_Name')
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        item_title = feed.item_title(nom)

        assert item_title == url.value

    def test_item_title_returns_url_title(self, rf):
        """If the url has no site name on record, return the title."""
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        url = factories.URLFactory(url_project=project, entity=nom.entity, attribute='Title')
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        item_title = feed.item_title(nom)

        assert item_title == url.value

    def test_item_title_returns_entity(self, rf):
        """If the URL has no site name or title on record, return the URL."""
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        item_title = feed.item_title(nom)

        assert item_title == nom.entity

    def test_item_description(self, rf):
        project = factories.ProjectFactory()
        nom = factories.SURTFactory(url_project=project, entity='www.example.com')
        factories.URLFactory(
            url_project=project,
            entity=nom.entity,
            attribute='Description',
            value='Home Page'
        )
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        item_description = feed.item_description(nom)

        assert item_description == 'www.example.com - Home Page'

    def test_item_description_returns_entity(self, rf):
        """If the URL has no description, return just the URL itself."""
        project = factories.ProjectFactory()
        nom = factories.SURTFactory(url_project=project)
        request = rf.get('/')

        feed = feeds.nomination_feed()
        feed.get_object(request, project.project_slug)
        item_description = feed.item_description(nom)

        assert item_description == nom.entity
