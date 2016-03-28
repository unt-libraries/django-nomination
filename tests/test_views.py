from datetime import date, datetime, timedelta

import pytest
import json

from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.conf import settings

from nomination import views, models
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

    def test_status_and_content_type(self, rf):
        request = rf.get('/')
        response = views.robot_ban(request)
        assert response.status_code == 200
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

    def test_status_ok(self, client):
        project = factories.ProjectFactory()
        response = client.get(reverse('project_urls', args=[project.project_slug]))
        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory()
        response = client.get(reverse('project_urls', args=[project.project_slug]))
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
        response = client.get(reverse('project_urls', args=[project.project_slug]))

        assert response.context['project'] == project
        assert response.context['url_count'] == 3
        assert response.context['nominator_count'] == 2
        assert 'browse_tup' in response.context


class TestUrlListing():

    @pytest.mark.parametrize('request_type', [
        'get',
        'post'
    ])
    def test_status_ok(self, client, request_type):
        entity = 'www.example.com'
        project = factories.ProjectFactory()
        factories.URLFactory(url_project=project, entity=entity)
        response = getattr(client, request_type)(
            reverse('url_listing', args=[project.project_slug, entity]))

        assert response.status_code == 200

    @pytest.mark.parametrize('request_type', [
        'get',
        'post'
    ])
    def test_status_ok_when_url_does_not_exist(self, client, request_type):
        entity = 'www.example.com'
        project = factories.ProjectFactory()
        response = getattr(client, request_type)(
            reverse('url_listing', args=[project.project_slug, entity]))

        assert response.status_code == 200

    @pytest.mark.parametrize('request_type, expected_template', [
        ('get', 'nomination/url_listing.html'),
        ('post', 'nomination/url_listing.html')
    ])
    def test_template_used(self, client, request_type, expected_template):
        entity = 'www.example.com'
        project = factories.ProjectFactory()
        factories.URLFactory(url_project=project, entity=entity)
        response = getattr(client, request_type)(
            reverse('url_listing', args=[project.project_slug, entity]))

        assert response.templates[0].name == expected_template

    @pytest.mark.parametrize('request_type, expected_template', [
        ('get', 'nomination/url_add.html'),
        ('post', 'nomination/url_add.html')
    ])
    def test_template_used_when_url_does_not_exist(self, client, request_type, expected_template):
        entity = 'www.example.com'
        project = factories.ProjectFactory()
        response = getattr(client, request_type)(
            reverse('url_listing', args=[project.project_slug, entity]))

        assert response.templates[0].name == expected_template

    def test_context_url_not_found(self, client):
        entity = 'http://www.example.com'
        project = factories.ProjectFactory()
        response = client.get(reverse('url_listing', args=[project.project_slug, entity]))
        expected_context = {
            'project': project,
            'form': views.URLForm({'url_value': entity}),
            'url_not_found': True,
            'metadata_vals': views.get_metadata(project),
            'form_errors': None,
            'summary_list': None,
            'json_data': None,
            'form_types': None,
            'institutions': views.get_look_ahead(project),
            'url_entity': entity,
        }

        for key in expected_context:
            assert str(response.context[key]) == str(expected_context[key])

    def test_base_context_values(self, client):
        """Test the context variables which are similar across different paths.

        These context variables do not change based on the specific path taken
        in the view, and so are being tested apart from the rest. The only time
        they may change is if the requested url does not actually exist, and that
        occurrence is covered in the previous test.
        """
        entity = u'http://www.example.com'
        entity_surt = u'http://(com,example,www,)'
        project = factories.ProjectFactory()
        project_metadata = factories.ProjectMetadataFactory(project=project)
        url = factories.URLFactory(url_project=project, entity=entity)
        factories.SURTFactory(
            url_project=project,
            entity=entity,
            value=entity_surt
        )
        related_urls = factories.SURTFactory.create_batch(
            1,
            url_project=project,
            entity=u'{}/main/page'.format(entity),
            value=u'{}/main/page'.format(entity_surt)
        )
        expected_context = {
            'project': project,
            'url_data': views.create_url_list(project, related_urls + [url]),
            'related_url_list': related_urls,
            'metadata_vals': views.get_metadata(project),
            'institutions': views.get_look_ahead(project),
            'form_types': json.dumps({project_metadata.metadata.name: project_metadata.form_type}),
        }
        response = client.get(reverse('url_listing', args=[project.project_slug, entity]))

        for key in expected_context:
            assert str(response.context[key]) == str(expected_context[key])

    def test_context_with_post(self, client):
        data = {
            'scope': 1,
            'nominator_name': 'John Doe',
            'nominator_email': 'here@there.com',
            'nominator_institution': 'UNT',
            'metadata': '2012-12-12'
        }
        entity = 'www.example.com'
        project = factories.ProjectFactory(registration_required=False)
        factories.ProjectMetadataFactory(
            project=project,
            metadata__name='metadata',
            form_type='date'
        )
        factories.URLFactory(url_project=project, entity=entity)
        response = client.post(
            reverse('url_listing', args=[project.project_slug, entity]),
            data
        )
        expected = {
            'scope_form': views.ScopeForm(data),
            'form_errors': '',
            'summary_list': [
                u'You have successfully nominated www.example.com',
                u'You have successfully added the metadata "2012-12-12" for www.example.com'
            ],
            'json_data': None,
        }

        for key in expected:
            assert str(response.context[key]) == str(expected[key])

    @pytest.mark.parametrize('reg_required, data, expected_errors', [
        (
            False,
            {'scope': 2},
            {'scope': [u'Select a valid choice. 2 is not one of the available choices.']}
        ),
        (
            False,
            {'scope': 1, 'nominator_name': 'John Doe', 'nominator_institution': 'UNT'},
            {
                'nominator_email': (
                    u'You must provide name, institution, and '
                    'email to affiliate your name or institution with nominations. Leave '
                    'all "Information About ' 'You" fields blank to remain anonymous.'
                )
            }
        ),
        (
            True,
            {'scope': 1, 'nominator_name': 'John Doe', 'nominator_institution': 'UNT'},
            {'nominator_email': u'This field is required.'}
        )
    ])
    def test_context_with_post_and_errors(self, client, reg_required, data, expected_errors):
        entity = 'www.example.com'
        project = factories.ProjectFactory(registration_required=reg_required)
        factories.URLFactory(url_project=project, entity=entity)
        response = client.post(
            reverse('url_listing', args=[project.project_slug, entity]),
            data
        )

        assert response.context['form_errors'] == expected_errors
        assert response.context['summary_list'] is None
        assert response.context['scope_form'].is_valid() is False
        assert sorted(json.loads(response.context['json_data'])) == sorted(
            [[key, [str(data[key])]] for key in data])

    def test_context_with_get(self, client):
        entity = u'http://www.example.com'
        entity_surt = u'http://(com,example,www,)'
        project = factories.ProjectFactory()
        factories.ProjectMetadataFactory(project=project)
        factories.URLFactory(url_project=project, entity=entity)
        factories.SURTFactory(
            url_project=project,
            entity=entity,
            value=entity_surt
        )
        factories.SURTFactory.create_batch(
            1,
            url_project=project,
            entity=u'{}/main/page'.format(entity),
            value=u'{}/main/page'.format(entity_surt)
        )

        expected_context = {
            'scope_form': views.ScopeForm(),
            'form_errors': None,
            'summary_list': None,
            'json_data': None
        }
        response = client.get(reverse('url_listing', args=[project.project_slug, entity]))

        for key in expected_context:
            assert str(response.context[key]) == str(expected_context[key])


class TestUrlSurt():

    def test_status_ok(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_surt(request, project.project_slug, 'a_surt')

        assert response.status_code == 200

    def test_raises_http404(self, rf):
        request = rf.get('/')
        with pytest.raises(Http404):
            views.url_surt(request, 'fake_slug', 'a_surt')

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

    @pytest.mark.parametrize('request_type, data_dict', [
        ('get', {}),
        ('post', {
            'nominator_name': 'Eddie',
            'nominator_institution': 'UNT',
            'nominator_email': 'someone@somewhere.com'
        })
    ])
    def test_status_ok(self, client, request_type, data_dict):
        project = factories.ProjectFactory()
        response = getattr(client, request_type)(
            reverse('url_add', args=[project.project_slug]), data_dict)
        assert response.status_code == 200

    def test_template_used(self, client):
        project = factories.ProjectFactory(registration_required=False)
        response = client.post(
            reverse('url_add', args=[project.project_slug]),
            {
                'nominator_name': 'Eddie',
                'nominator_institution': 'UNT',
                'nominator_email': 'someone@somewhere.com'
            }
        )

        assert response.templates[0].name == 'nomination/url_add.html'

    def test_base_context_values(self, client):
        entity = u'http://www.example.com'
        entity_surt = u'http://(com,example,www,)'
        project = factories.ProjectFactory()
        project_metadata = factories.ProjectMetadataFactory(project=project)
        factories.URLFactory(url_project=project, entity=entity)
        factories.SURTFactory(
            url_project=project,
            entity=entity,
            value=entity_surt
        )
        factories.SURTFactory.create_batch(
            1,
            url_project=project,
            entity=u'{}/main/page'.format(entity),
            value=u'{}/main/page'.format(entity_surt)
        )
        expected_context = {
            'project': project,
            'form': views.URLForm(),
            'metadata_vals': views.get_metadata(project),
            'institutions': views.get_look_ahead(project),
            'form_types': json.dumps({project_metadata.metadata.name: project_metadata.form_type}),
        }
        response = client.get(reverse('url_add', args=[project.project_slug]))

        for key in expected_context:
            assert str(response.context[key]) == str(expected_context[key])

    def test_context_with_get(self, client):
        entity = u'http://www.example.com'
        entity_surt = u'http://(com,example,www,)'
        project = factories.ProjectFactory()
        factories.ProjectMetadataFactory(project=project)
        factories.URLFactory(url_project=project, entity=entity)
        factories.SURTFactory(
            url_project=project,
            entity=entity,
            value=entity_surt
        )
        factories.SURTFactory.create_batch(
            1,
            url_project=project,
            entity=u'{}/main/page'.format(entity),
            value=u'{}/main/page'.format(entity_surt)
        )

        expected_context = {
            'form_errors': None,
            'summary_list': None,
            'json_data': None,
            'url_entity': None
        }
        response = client.get(reverse('url_add', args=[project.project_slug]))

        for key in expected_context:
            assert str(response.context[key]) == str(expected_context[key])

    def test_context_with_post(self, client):
        entity = 'http://www.example.com'
        data = {
            'url_value': entity,
            'nominator_name': 'John Doe',
            'nominator_email': 'here@there.com',
            'nominator_institution': 'UNT',
            'metadata': '2012-12-12'
        }
        project = factories.ProjectFactory(registration_required=False)
        factories.ProjectMetadataFactory(
            project=project,
            metadata__name='metadata',
            form_type='date'
        )
        factories.URLFactory(url_project=project, entity=entity)
        response = client.post(
            reverse('url_add', args=[project.project_slug]),
            data
        )
        expected = {
            'form_errors': '',
            'summary_list': [
                u'You have successfully nominated http://www.example.com',
                u'You have successfully added the metadata "2012-12-12" for http://www.example.com'
            ],
            'json_data': None,
            'url_entity': entity
        }

        for key in expected:
            assert str(response.context[key]) == str(expected[key])

    @pytest.mark.parametrize('reg_required, data, expected_errors', [
        (
            False,
            {'nominator_name': '', 'nominator_institution': '', 'nominator_email': ''},
            {'url_value': ['This field is required.']}
        ),
        (
            False,
            {
                'url_value': 'http://www.example.com',
                'nominator_name': 'John Doe',
                'nominator_institution': 'UNT',
                'nominator_email': '',
            },
            {
                'nominator_email': (
                    u'You must provide name, institution, and '
                    'email to affiliate your name or institution with nominations. Leave '
                    'all "Information About ' 'You" fields blank to remain anonymous.'
                )
            }
        ),
        (
            True,
            {
                'url_value': 'http://www.example.com',
                'nominator_name': 'John Doe',
                'nominator_institution': 'UNT',
                'nominator_email': ''
            },
            {'nominator_email': u'This field is required.'}
        )
    ])
    def test_context_with_post_and_errors(self, client, reg_required, data, expected_errors):
        entity = 'http://www.example.com'
        project = factories.ProjectFactory(registration_required=reg_required)
        factories.URLFactory(url_project=project, entity=entity)
        response = client.post(
            reverse('url_add', args=[project.project_slug]),
            data
        )
        expected = {
            'form_errors': expected_errors,
            'summary_list': None,
            'json_data': None,
            'url_entity': None
        }

        assert response.context['form_errors'] == expected['form_errors']
        assert response.context['summary_list'] == expected['summary_list']
        assert sorted(json.loads(response.context['json_data'])) == sorted(
            [[key, [data[key]]] for key in data])
        assert response.context['url_entity'] == expected['url_entity']


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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.browse_json(request, project.project_slug, '')

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.search_json(request, project.project_slug)

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_report(request, project.project_slug)

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.surt_report(request, project.project_slug)

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_score_report(request, project.project_slug)

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_date_report(request, project.project_slug)

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.url_nomination_report(request, project.project_slug)

        assert response.status_code == 200
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

    @pytest.mark.parametrize('metadata_with_valueset', [
        True,
        False
    ])
    def test_context(self, client, metadata_with_valueset):
        if metadata_with_valueset:
            project = factories.ProjectWithMetadataFactory(metadata1=None)
        else:
            project = factories.ProjectWithMetadataFactory(metadata2=None)
        metadata = models.Project_Metadata.objects.first().metadata
        value = (
            metadata.value_sets.first().values.first().key if metadata_with_valueset
            else u'something'
        )
        factories.URLFactory.create_batch(
            3,
            url_project=project,
            attribute=metadata.name,
            value=value
        )
        response = client.get(reverse('field_report', args=[project.project_slug, metadata.name]))

        assert response.context['project'] == project
        assert str(response.context['valdic']) == str([(value, 3)])
        assert response.context['namelist'] == (
            [(models.Value.objects.filter(key=value)[0].value, 3, value)] if metadata_with_valueset
            else [(value, 3, value)]
        )
        assert response.context['field'] == metadata.name


class TestValueReport():

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.value_report(request, project.project_slug, '', '')

        assert response.status_code == 200
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
        ('nominator', 'name'),
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.nominator_url_report(request, project.project_slug, '', 1)

        assert response.status_code == 200
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

    def test_status_and_content_type(self, rf):
        project = factories.ProjectFactory()
        request = rf.get('/')
        response = views.project_dump(request, project.project_slug)

        assert response.status_code == 200
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
