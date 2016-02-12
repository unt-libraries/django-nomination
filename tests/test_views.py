from datetime import date, datetime, timedelta

import pytest
import json

from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.conf import settings

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
        factories.URLFactory(url_project=project, attribute='surt')
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

    @pytest.mark.parametrize('create_url', [
        False,
        True
    ])
    def test_status_ok(self, rf, create_url):
        entity = 'www.example.com'
        project = factories.ProjectFactory()
        if create_url:
            factories.URLFactory(url_project=project, entity=entity)
        request = rf.get('/')
        response = views.url_listing(request, project.project_slug, entity)

        assert response.status_code == 200

    @pytest.mark.parametrize('create_url, expected_template', [
        (False, 'nomination/url_add.html'),
        (True, 'nomination/url_listing.html')
    ])
    def test_template_used(self, client, create_url, expected_template):
        entity = 'www.example.com'
        project = factories.ProjectFactory()
        if create_url:
            factories.URLFactory(url_project=project, entity=entity)
        response = client.get(reverse('url_listing', args=[project.project_slug, entity]))

        assert response.templates[0].name == expected_template


class TestUrlSurt():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_surt(request, project.project_slug, 'a_surt')

        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        response = client.get(reverse('url_surt', args=[project.project_slug, 'a surt']))
        assert response.templates[0].name == 'nomination/url_surt.html'

    @pytest.mark.parametrize('surt_root, surt, url_list_len, letter', [
        ('http://(com,e', 'http://(com,example,www)', 1, 'e'),
        ('http://(com,example,www)', 'http://(com,example,www)', 1, False),
        ('http://(com,a', 'http://(com,example,www)', 0, 'a'),
        ('http://(com,apples,www)', 'http://(com,example,www)', 0, False)
    ])
    def test_context(self, client, surt_root, surt, url_list_len, letter):
        project = factories.ProjectFactory()
        url = factories.URLFactory(
            url_project=project,
            attribute='surt',
            value=surt
        )
        response = client.get(reverse('url_surt', args=[project.project_slug, surt_root]))

        assert response.context['surt'] == surt_root
        assert response.context['project'] == project
        assert len(response.context['url_list']) == url_list_len
        if url_list_len == 1:
            assert response.context['url_list'][0] == url
        assert response.context['letter'] == letter
        assert response.context['browse_domain'] == 'com'
        assert len(response.context['browse_dict']) == 1
        for each in response.context['browse_dict']['com']:
            if each[1] is not None:
                assert each == ('E', 'http://(com,e')


class TestUrlAdd():

    def test_status_ok(self, rf):
        pass

    def test_template_used(self, client):
        pass

    def test_context(self, client):
        pass


class TestProjectAbout():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.project_about(request, project.project_slug)

        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        response = client.get(reverse('project_about', args=[project.project_slug]))
        assert response.templates[0].name == 'nomination/project_about.html'

    @pytest.mark.parametrize('nomination_end, show_bookmarklets', [
        (datetime.now() - timedelta(days=1), False),
        (datetime.now() + timedelta(days=1), True)
    ])
    def test_context(self, client, nomination_end, show_bookmarklets):
        project = factories.ProjectFactory(nomination_end=nomination_end)
        factories.URLFactory(url_project=project, attribute='surt')
        factories.NominatedURLFactory.create_batch(2, url_project=project, value=1)
        current_host = Site.objects.get(id=settings.SITE_ID)
        response = client.get(reverse('project_about', args=[project.project_slug]))

        assert response.context['project'] == project
        assert response.context['url_count'] == 1
        assert response.context['nominator_count'] == 2
        assert response.context['current_host'] == current_host
        assert response.context['show_bookmarklets'] == show_bookmarklets


class TestBrowseJson():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.browse_json(request, project.project_slug, '')

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.browse_json(request, project.project_slug, '')

        assert response['Content-Type'] == 'application/json'

    @pytest.mark.parametrize('request_type, kwargs, id, text', [
        ('get', {'root': 'com,'}, 'com,example,',
         '<a href="surt/http://(com,example">com,example</a>'),
        ('get', {'root': 'source'}, 'com,', 'com'),
        ('get', {}, 'com,', 'com'),
        ('post', {}, 'com,', 'com')
    ])
    def test_json_string(self, rf, request_type, kwargs, id, text):
        project = factories.ProjectFactory()
        factories.URLFactory(
            url_project=project,
            attribute='surt',
            value='http://(com,example,www)'
        )
        request = getattr(rf, request_type)('/', kwargs)
        response = views.browse_json(request, project.project_slug, '')

        assert json.loads(response.content) == [{
            'hasChildren': True,
            'id': id,
            'text': text
        }]


class TestSearchJson():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.search_json(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.search_json(request, project.project_slug)

        assert response['Content-Type'] == 'application/json'


class TestReportsView():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.reports_view(request, project.project_slug)

        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        response = client.get(reverse('reports_view', args=[project.project_slug]))
        assert response.templates[0].name == 'nomination/reports.html'

    def test_context(self, client):
        project = factories.ProjectFactory()
        attrs = [x.attribute for x in factories.URLFactory.create_batch(3, url_project=project)]
        response = client.get(reverse('reports_view', args=[project.project_slug]))

        assert response.context['project'] == project
        assert len(response.context['metadata_fields']) == 3
        for each in response.context['metadata_fields']:
            assert each[0] in attrs


class TestUrlReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_report(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_report(request, project.project_slug)

        assert response['Content-Type'] == 'text/plain; charset="UTF-8"'

    def test_report_text(self, rf):
        project = factories.ProjectFactory()
        urls = factories.URLFactory.create_batch(3, url_project=project, attribute='surt')
        request = rf.get('/')
        response = views.url_report(request, project.project_slug)

        assert '#This list of urls' in response.content
        for each in urls:
            assert each.entity in response.content


class TestSurtReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.surt_report(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.surt_report(request, project.project_slug)

        assert response['Content-Type'] == 'text/plain; charset="UTF-8"'

    def test_report_text(self, rf):
        project = factories.ProjectFactory()
        urls = factories.URLFactory.create_batch(3, url_project=project, attribute='surt')
        request = rf.get('/')
        response = views.surt_report(request, project.project_slug)

        assert '#This list of SURTs' in response.content
        for each in urls:
            assert each.value in response.content


class TestUrlScoreReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_score_report(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_score_report(request, project.project_slug)

        assert response['Content-Type'] == 'text/plain; charset="UTF-8"'

    def test_report_text(self, rf):
        project = factories.ProjectFactory()
        urls = factories.NominatedURLFactory.create_batch(3, url_project=project)
        request = rf.get('/')
        response = views.url_score_report(request, project.project_slug)

        assert '#This list of URLs' in response.content
        for each in urls:
            assert '{0};"{1}"\n'.format(each.value, each.entity) in response.content


class TestUrlDateReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_date_report(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_date_report(request, project.project_slug)

        assert response['Content-Type'] == 'text/plain; charset="UTF-8"'

    def test_report_text(self, rf):
        project = factories.ProjectFactory()
        urls = factories.NominatedURLFactory.create_batch(3, url_project=project)
        request = rf.get('/')
        response = views.url_date_report(request, project.project_slug)

        assert '#This list of URLs' in response.content
        for each in urls:
            assert '{0};"{1}";{2}\n'.format(
                each.date.replace(microsecond=0).isoformat(),
                each.entity,
                each.value
            ) in response.content


class TestUrlNominationReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_nomination_report(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_nomination_report(request, project.project_slug)

        assert response['Content-Type'] == 'text/plain; charset="UTF-8"'

    def test_report_text(self, rf):
        project = factories.ProjectFactory()
        urls = factories.NominatedURLFactory.create_batch(3, url_project=project)
        request = rf.get('/')
        response = views.url_nomination_report(request, project.project_slug)

        assert '#This list of URLs' in response.content
        for each in urls:
            assert '1;"{0}"\n'.format(each.entity) in response.content


class TestFieldReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.field_report(request, project.project_slug, '')

        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        response = client.get(reverse('field_report', args=[project.project_slug, 'blah']))
        assert response.templates[0].name == 'nomination/metadata_report.html'

    def test_context(self, client):
        pass


class TestValueReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.value_report(request, project.project_slug, '', '')

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.value_report(request, project.project_slug, '', '')

        assert response['Content-Type'] == 'text/plain;'

    @pytest.mark.parametrize('val, url_value', [
        ('asdf', 'asdf'),
        ('asdf', 'asdf/')
    ])
    def test_report_text(self, rf, val, url_value):
        project = factories.ProjectFactory()
        field = 'qwerty'
        urls = factories.URLFactory.create_batch(
            3,
            url_project=project,
            attribute=field,
            value=url_value
        )
        request = rf.get('/')
        response = views.value_report(request, project.project_slug, field, val)

        assert '#This list of URLs' in response.content
        for each in urls:
            assert each.entity in response.content


class TestNominatorReport():

    @pytest.mark.parametrize('field', [
        'nominator',
        'institution'
    ])
    def test_status_ok(self, rf, field):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.nominator_report(request, project.project_slug, field)

        assert response.status_code == 200

    @pytest.mark.parametrize('field', [
        'nominator',
        'institution'
    ])
    def test_template_used(self, client, field):
        project = factories.ProjectFactory()
        response = client.get(reverse('nominator_report', args=[project.project_slug, field]))
        assert response.templates[0].name == 'nomination/nominator_report.html'

    @pytest.mark.parametrize('field, field_name', [
        ('nominator','name'),
        ('institution', 'institution')
    ])
    def test_context(self, client, field, field_name):
        project = factories.ProjectFactory()
        urls = factories.NominatedURLFactory.create_batch(
            3,
            url_project=project,
            value=1
        )
        response = client.get(reverse('nominator_report', args=[project.project_slug, field]))

        assert response.context['project'] == project
        assert len(response.context['valdic']) == 3
        for each in urls:
            assert (getattr(each.url_nominator, 'nominator_{0}'.format(field_name)),
                    1, each.url_nominator.id) in response.context['valdic']
        assert response.context['field'] == field


class TestNominatorUrlReport():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.nominator_url_report(request, project.project_slug, '', 1)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.nominator_url_report(request, project.project_slug, '', 1)

        assert response['Content-Type'] == 'text/plain; charset="UTF-8"'

    @pytest.mark.parametrize('field', [
        'nominator',
        'institution',
        'neither'
    ])
    def test_report_text(self, rf, field):
        project = factories.ProjectFactory()
        url = factories.NominatedURLFactory(url_project=project, value=1)
        request = rf.get('/')
        response = views.nominator_url_report(
            request,
            project.project_slug,
            field, url.url_nominator.id
        )

        assert '#This list of URLs' in response.content
        assert url.entity in response.content


class TestProjectDump():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.project_dump(request, project.project_slug)

        assert response.status_code == 200

    def test_mimetype(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.project_dump(request, project.project_slug)

        assert response['Content-Type'] == 'application/json; charset=utf-8'

    def test_content_disposition(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.project_dump(request, project.project_slug)

        assert response['Content-Disposition'] == 'attachment; filename={0}_urls.json'.format(
            project.project_slug)

    def test_response_content(self, rf):
        project = factories.ProjectFactory()
        url = factories.URLFactory(url_project=project)
        request = rf.get('/')
        response = views.project_dump(request, project.project_slug)
        expected = {
            url.entity: {
                'attributes': {
                    url.attribute: [url.value]
                },
                'nomination_count': 0,
                'nomination_score': 0,
                'nominators': []
            }
        }

        assert json.loads(response.content) == expected
