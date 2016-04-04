import pytest
import xml.etree.ElementTree as ET

from django import http
from django.utils.http import urlquote
from django.core.urlresolvers import reverse
from django.contrib.syndication.views import FeedDoesNotExist

from nomination import feeds
from . import factories


pytestmark = pytest.mark.django_db
ns = {'feed': 'http://www.w3.org/2005/Atom'}


class TestURLFeed:

    @pytest.fixture
    def setup_feed(self, client):
        project = factories.ProjectFactory()
        surts = factories.URLFactory.create_batch(
            3,
            url_project=project,
            attribute='surt'
        )
        response = client.get(reverse('url_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)

        return (project, surts, feed_root)

    def test_title(self, setup_feed):
        project, _, feed_root = setup_feed
        expected = 'Latest URLs for {0}'.format(project.project_name)
        assert feed_root.find('feed:title', ns).text == expected

    def test_link(self, setup_feed):
        project, _, feed_root = setup_feed
        expected = 'http://example.com/nomination/{0}/feed/urls/'.format(project.project_slug)
        link = feed_root.find('feed:link', ns)

        assert link.attrib['rel'] == 'alternate'
        assert link.attrib['href'] == link.attrib['href'] == expected

    @pytest.mark.xfail(reason="Atom feeds should use the 'subtitle' element, not 'description'.")
    def test_description(self, setup_feed):
        project, _, feed_root = setup_feed
        expected = 'RSS feed for the most recent URLs added to {0}.'.format(project.project_name)
        assert feed_root.find('feed:description', ns).text == expected


    def test_num_items(self, setup_feed):
        _, _, feed_root = setup_feed
        entries = feed_root.findall('feed:entry', ns)
        assert  len(entries) == 3

    @pytest.mark.xfail(reason='Manual use of urlquote inside of reverse produces different URL.')
    def test_item_link(self, setup_feed):
        project, urls, feed_root = setup_feed
        expected = 'http://example.com/nomination/{0}/url/{1}/'.format(
            project.project_slug,
            urlquote(urls[2].entity)
        )
        link = feed_root.find('./feed:entry/feed:link', ns).attrib['href']
        assert link == expected

    @pytest.mark.xfail(reason="Django < 1.7 incorrectly sets the 'updated' field using pubdate.")
    def test_item_pubdate(self, setup_feed):
        _, urls, feed_root = setup_feed
        pubdate = feed_root.find('./feed:entry/feed:published', ns).text
        assert pubdate == urls[2].date

    def test_item_title_when_url_has_site_name(self, client):
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        url = factories.URLFactory(
            url_project=project,
            entity=surt.entity,
            attribute='Site_Name'
        )
        response = client.get(reverse('url_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)
        title = feed_root.find('./feed:entry/feed:title', ns).text
        assert title == url.value

    def test_item_title_when_url_has_title(self, client):
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        url = factories.URLFactory(
            url_project=project,
            entity=surt.entity,
            attribute='Title'
        )
        response = client.get(reverse('url_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)
        title = feed_root.find('./feed:entry/feed:title', ns).text
        assert title == url.value

    def test_item_title_when_url_has_no_site_name_or_title(self, setup_feed):
        _, urls, feed_root = setup_feed
        title = feed_root.find('./feed:entry/feed:title', ns).text
        assert title == urls[2].entity

    def test_item_description(self, client):
        project = factories.ProjectFactory()
        surt = factories.SURTFactory(url_project=project)
        url = factories.URLFactory(
            url_project=project,
            entity=surt.entity,
            attribute='Description'
        )
        response = client.get(reverse('url_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)
        description = feed_root.find('./feed:entry/feed:summary', ns).text
        assert description == '{0} - {1}'.format(url.entity, url.value)

    def test_item_description_when_url_has_no_description(self, setup_feed):
        _, urls, feed_root = setup_feed
        description = feed_root.find('./feed:entry/feed:summary', ns).text
        assert description == urls[2].entity


class TestNominationFeed:

    @pytest.fixture
    def setup_feed(self, client):
        project = factories.ProjectFactory()
        noms = factories.NominatedURLFactory.create_batch(3, url_project=project)
        response = client.get(reverse('nomination_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)

        return (project, noms, feed_root)

    def test_title(self, setup_feed):
        project, _, feed_root = setup_feed
        expected = 'Most Recent Nominations for {0}'.format(project.project_name)
        assert feed_root.find('feed:title', ns).text == expected

    def test_link(self, setup_feed):
        project, _, feed_root = setup_feed
        expected = 'http://example.com/nomination/{0}/feed/nominations/'.format(project.project_slug)
        link = feed_root.find('feed:link', ns)

        assert link.attrib['rel'] == 'alternate'
        assert link.attrib['href'] == link.attrib['href'] == expected

    @pytest.mark.xfail(reason='Atom feeds should use the "subtitle" element, not "description".')
    def test_description(self, setup_feed):
        project, _, feed_root = setup_feed
        expected = ('RSS feed for the most recently nomtly nominated URLs for {0}. Includes '
                    'newly added URLs and subsequent nominations of those URLs'
                    .format(project.project_name))
        assert feed_root.find('feed:description', ns).text == expected

    def test_items(self, setup_feed):
        _, _, feed_root = setup_feed
        entries = feed_root.findall('feed:entry', ns)
        assert  len(entries) == 3

    @pytest.mark.xfail(reason='Manual use of urlquote inside of reverse produces different URL.')
    def test_item_link(self, setup_feed):
        project, noms, feed_root = setup_feed
        expected = 'http://example.com/nomination/{0}/url/{1}/'.format(
            project.project_slug,
            urlquote(noms[2].entity)
        )
        link = feed_root.find('./feed:entry/feed:link', ns).attrib['href']
        assert link == expected

    @pytest.mark.xfail(reason="Django < 1.7 incorrectly sets the 'updated' field using pubdate.")
    def test_item_pubdate(self, setup_feed):
        _, noms, feed_root = setup_feed
        pubdate = feed_root.find('./feed:entry/feed:published', ns).text
        assert pubdate == noms[2].date

    def test_item_title_when_nom_has_site_name(self, client):
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        url = factories.URLFactory(
            url_project=project,
            entity=nom.entity,
            attribute='Site_Name'
        )
        response = client.get(reverse('nomination_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)
        title = feed_root.find('./feed:entry/feed:title', ns).text
        assert title == url.value

    def test_item_title_when_nom_has_title(self, client):
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        url = factories.URLFactory(
            url_project=project,
            entity=nom.entity,
            attribute='Title'
        )
        response = client.get(reverse('nomination_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)
        title = feed_root.find('./feed:entry/feed:title', ns).text
        assert title == url.value

    def test_item_title_when_nom_has_no_site_name_or_title(self, setup_feed):
        _, noms, feed_root = setup_feed
        title = feed_root.find('./feed:entry/feed:title', ns).text
        assert title == noms[2].entity

    def test_item_description(self, client):
        project = factories.ProjectFactory()
        nom = factories.NominatedURLFactory(url_project=project)
        url = factories.URLFactory(
            url_project=project,
            entity=nom.entity,
            attribute='Description'
        )
        response = client.get(reverse('nomination_feed', args=[project.project_slug]))
        feed_root = ET.fromstring(response.content)
        description = feed_root.find('./feed:entry/feed:summary', ns).text
        assert description == '{0} - {1}'.format(url.entity, url.value)

    def test_item_description_when_url_has_none(self, setup_feed):
        _, noms, feed_root = setup_feed
        description = feed_root.find('./feed:entry/feed:summary', ns).text
        assert description == noms[2].entity
