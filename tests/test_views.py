from datetime import date

import pytest

from django.http import Http404
from django.core.urlresolvers import reverse

from nomination import views
from . import factories


pytestmark = pytest.mark.django_db


class TestProjectListing():

    def test_status_ok(self, rf):
        request = rf.get('/')
        response = views.project_listing(request)
        assert response.status_code == 200

    def test_template_used(self, client):
        response = client.get(reverse('project_listing'))
        assert response.templates[0].name == 'nomination/project_listing.html'

    def test_context(self, client):
        active_project = factories.ProjectFactory()
        past_project = factories.ProjectFactory(
            project_start=date(2015, 1, 1),
            project_end=date(2015, 1, 2)
        )
        response = client.get(reverse('project_listing'))

        assert len(response.context['active_list']) == 1
        assert response.context['active_list'][0] == active_project
        assert len(response.context['past_list']) == 1
        assert response.context['past_list'][0] == past_project


class TestRobotBan():

    def test_status_ok(self, rf):
        request = rf.get('/')
        response = views.robot_ban(request)
        assert response.status_code == 200

    def test_mimetype(self, rf):
        request = rf.get('/')
        response = views.robot_ban(request)
        assert response['Content-Type'] == 'text/plain'


class TestNominationAbout():

    def test_status_ok(self, rf):
        request = rf.get('/')
        response = views.nomination_about(request)
        assert response.status_code == 200

    def test_template_used(self, client):
        response = client.get(reverse('nomination_about'))
        assert response.templates[0].name == 'nomination/about.html'


class TestNominationHelp():

    def test_status_ok(self, rf):
        request = rf.get('/')
        response = views.nomination_help(request)
        assert response.status_code == 200

    def test_template_used(self, client):
        response = client.get(reverse('nomination_help'))
        assert response.templates[0].name == 'nomination/help.html'


class TestUrlLookup():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        url = factories.URLFactory(url_project=project, attribute='surt')
        request = rf.post('/', {'search-url-value': url.entity, 'partial-search': ''})
        response = views.url_lookup(request, project.project_slug)

        assert response.status_code == 200

    def test_redirects(self, rf):
        project = factories.ProjectFactory()
        request = rf.post('/', {'search-url-value': 'a_url'})
        response = views.url_lookup(request, project.project_slug)

        assert response.status_code == 302
        assert response['Location'] == '/nomination/{0}/url/a_url/'.format(project.project_slug)

    def test_raises_http404_if_not_post(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')

        with pytest.raises(Http404):
            views.url_lookup(request, project.project_slug)

    def test_raises_http404_with_no_search_url_value(self, rf):
        project = factories.ProjectFactory()
        url = factories.URLFactory(url_project=project, attribute='surt')
        request = rf.post('/', {'partial-search': ''})

        with pytest.raises(Http404):
            views.url_lookup(request, project.project_slug)

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        url = factories.URLFactory(url_project=project, attribute='surt')
        response = client.post(
            reverse('url_lookup', args=[project.project_slug]),
            {'search-url-value': url.entity, 'partial-search': ''}
        )

        assert response.templates[0].name == 'nomination/url_search_results.html'

    def test_context(self, client):
        project = factories.ProjectFactory()
        url = factories.URLFactory(url_project=project, attribute='surt')
        response = client.post(
            reverse('url_lookup', args=[project.project_slug]),
            {'search-url-value': url.entity, 'partial-search': ''}
        )

        assert response.context['project'] == project
        assert len(response.context['url_list']) == 1
        assert response.context['url_list'][0] == url


class TestProjectUrls():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.project_urls(request, project.project_slug)

        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        response = client.post(reverse('project_urls', args=[project.project_slug]))
        assert response.templates[0].name == 'nomination/project_urls.html'

    def test_context(self, client):
        project = factories.ProjectFactory()
        factories.URLFactory.create_batch(
            3,
            url_project=project,
            attribute='surt',
            value='http://(com,example.www)'
        )
        factories.NominatedURLFactory.create_batch(
            2,
            url_project=project,
            value=1
        )
        response = client.post(reverse('project_urls', args=[project.project_slug]))

        assert response.context['project'] == project
        assert response.context['url_count'] == 3
        assert response.context['nominator_count'] == 2
        for key, value in response.context['browse_tup']:
            assert key == 'com'
            for each in value:
                if each[1] is not None:
                    assert each == ('E', 'http://(com,e')


class TestUrlListing():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestUrlSurt():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestUrlAdd():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestProjectAbout():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestBrowseJson():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestSearchJson():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestReportsView():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestUrlReport():

    def test_status_ok(self, rf):
        pass

    def test_raises_http404(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestSurtReport():

    def test_status_ok(self, rf):
        pass

    def test_raises_http404(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestUrlScoreReport():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestUrlDateReport():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestUrlNominationReport():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestFieldReport():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestValueReport():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestNominatorReport():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestNominatorUrlReport():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass


class TestProjectDump():

    def test_status_ok(self, rf):
        pass

    def test_mimetype(self, rf):
        pass
