import pytest

from django import http
from django.contrib.syndication.views import FeedDoesNotExist

from nomination import feeds
from . import factories


pytestmark = pytest.mark.django_db


class TestURLFeed:

    def test_get_object(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.url_feed()
        returned = feed.get_object(request, project.project_slug)

        assert returned == project

    def test_get_object_raises_http404(self, rf):
        request = rf.get('/')
        feed = feeds.url_feed()

        with pytest.raises(http.Http404):
            feed.get_object(request, 'does_not_exist')

    def test_title(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.url_feed()
        feed(request, project.project_slug)
        returned = feed.title(project)

        assert returned == 'Latest URLs for {}'.format(project.project_name)

    def test_link(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.url_feed()
        feed(request, project.project_slug)
        returned = feed.link(project)

        assert returned == '/nomination/slug/feed/urls/'

    def test_link_returns_feed_does_not_exist(self, rf):
        request = rf.get('/')
        project = ''
        feed = feeds.url_feed()
        with pytest.raises(FeedDoesNotExist):
            feed.link(project)

    def test_description(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.url_feed()
        feed(request, project.project_slug)
        returned = feed.description(project)

        assert returned == 'RSS feed for the most recent URLs added to {}.'.format(project.project_name)

    def test_items(self, rf):
        pass

    def test_item_link(self):
        pass

    def test_item_pubdate(self):
        pass

    def test_item_title(self):
        pass

    def test_item_description(self):
        pass


class TestNominationFeed:

    def test_get_object(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.nomination_feed()
        returned = feed.get_object(request, project.project_slug)

        assert returned == project

    def test_get_object_raises_http404(self, rf):
        request = rf.get('/')
        feed = feeds.nomination_feed()

        with pytest.raises(http.Http404):
            feed.get_object(request, 'does_not_exist')

    def test_title(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.nomination_feed()
        feed(request, project.project_slug)
        returned = feed.title(project)

        assert returned == 'Most Recent Nominations for {}'.format(project.project_name)

    def test_link(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.nomination_feed()
        feed(request, project.project_slug)
        returned = feed.link(project)

        assert returned == '/nomination/slug/feed/nominations/'

    def test_description(self, rf):
        request = rf.get('/')
        project = factories.ProjectFactory(project_slug='slug')
        feed = feeds.nomination_feed()
        feed(request, project.project_slug)
        returned = feed.description(project)

        assert returned == ('RSS feed for the most recently nominated URLs for {}. Includes newly '
                            'added URLs and subsequent nominations of those URLs.'
                            .format(project.project_name))

    def test_items(self):
        pass

    def test_item_link(self):
        pass

    def test_item_pubdate(self):
        pass

    def test_item_title(self):
        pass

    def test_item_description(self):
        pass
