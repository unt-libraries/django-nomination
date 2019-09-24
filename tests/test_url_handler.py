import re
import json
from string import digits, ascii_uppercase, capwords
import datetime

from django import http
from django.conf import settings
from django.db import transaction

import pytest

from nomination import url_handler, models
from . import factories


pytestmark = pytest.mark.django_db
alnum_list = sorted(digits + ascii_uppercase)


class TestAlphabeticalBrowse():

    def test_returns_browse_dict(self):
        surts = {
            'A': ('http://(org,alarm,)', '(org,a'),
            'C': ('http://(org,charlie,)', '(org,c'),
            '1': ('http://(org,123,)', '(org,1')
        }
        project = factories.ProjectFactory()
        # Create the surts we're expecting to see represented in the returned dict.
        [factories.SURTFactory(url_project=project, value=surts[key][0]) for key in surts]
        expected = {
            'org': [(char, surts[char][1] if surts.get(char) else None) for char in alnum_list]
        }
        # Create another unrelated SURT to make sure we aren't grabbing everything.
        factories.SURTFactory()
        results = url_handler.alphabetical_browse(project)

        assert results == expected

    @pytest.mark.parametrize('surt, expected', [
        ('http://(,)', {}),
        ('http://(org,)', {'org': [(char, None) for char in alnum_list]})
    ])
    def test_no_valid_surts_found(self, surt, expected):
        project = factories.ProjectFactory()
        factories.SURTFactory(url_project=project, value=surt)
        results = url_handler.alphabetical_browse(project)

        assert results == expected

    def test_project_not_found(self):
        project = 'not a real project'
        with pytest.raises(http.Http404):
            url_handler.alphabetical_browse(project)


class TestGetMetadata():

    def test_returns_metadata_list(self):
        project = factories.ProjectFactory()
        vals = [mdv.metadata for mdv in factories.MetadataValuesFactory.create_batch(3)]
        proj_metadata = [
            factories.ProjectMetadataFactory(project=project, metadata=val)
            for val in vals
        ]
        expected = [
            (pm, [models.Metadata_Values.objects.get(metadata=pm.metadata).value])
            for pm in proj_metadata
        ]
        results = url_handler.get_metadata(project)

        for each in results:
            assert (each[0], list(each[1])) in expected

    def test_metadata_list_includes_valueset_values(self):
        project = factories.ProjectFactory()
        valset = factories.ValuesetFactory()
        vals = [factories.ValuesetValuesFactory(valueset=valset).value for i in range(3)]
        metadata = factories.MetadataFactory(value_sets=[valset])
        factories.ProjectMetadataFactory(project=project, metadata=metadata)
        results = url_handler.get_metadata(project)

        for _, value_iter in results:
            assert (val_iter in vals for val_iter in list(value_iter))


@pytest.mark.parametrize('posted_data, processed_posted_data, expected', [
    (
        {'color': ['blue', 'other_specify']},
        {'color': ['blue', 'other_specify'], 'color_other': 'magenta'},
        {'color': ['blue', 'magenta'], 'color_other': 'magenta'}
    ),
    (
        {'color': ['blue', 'other_specify']},
        {'color': ['blue', 'other_specify']},
        {'color': ['blue']}
    ),
    (
        {'color': ['blue', 'green']},
        {'color': ['blue', 'green']},
        {'color': ['blue', 'green']}
    ),
    (
        {'color': ['other_specify']},
        {'color': 'other_specify', 'color_other': 'magenta'},
        {'color': 'magenta', 'color_other': 'magenta'}
    ),
    pytest.param({'color': ['other_specify']}, {'color': 'other_specify'}, {},
                 marks=pytest.mark.xfail)
])
def test_handle_metadata(rf, posted_data, processed_posted_data, expected):
    request = rf.post('/', posted_data)
    assert url_handler.handle_metadata(request, processed_posted_data) == expected


class TestValidateDate():

    @pytest.mark.parametrize('date_str', [
        '2006-10-25',
        '10/25/2006',
        '10/25/06',
        'Oct 25 2006',
        'Oct 25, 2006',
        '25 Oct 2006',
        '25 Oct, 2006',
        'October 25 2006',
        'October 25, 2006',
        '25 October 2006',
        '25 October, 2006'
    ])
    def test_returns_valid_date(self, date_str):
        assert isinstance(url_handler.validate_date(date_str), datetime.date)

    def test_returns_none_with_invalid_date(self):
        date_str = '2006, Oct 25'
        assert url_handler.validate_date(date_str) is None


class TestAddURL():

    def test_returns_expected(self):
        project = factories.ProjectWithMetadataFactory()
        attribute_name = project.metadata.first().name
        value = 'some_value'
        form_data = {
            'url_value': 'http://www.example.com',
            'nominator_email': 'somebody@someplace.com',
            'nominator_name': 'John Lambda',
            'nominator_institution': 'UNT',
            attribute_name: value
        }
        expected = [
            'You have successfully nominated {0}'.format(form_data['url_value']),
            'You have successfully added the {0} "{1}" for {2}'.format(
                attribute_name, value, form_data['url_value'])
        ]

        assert url_handler.add_url(project, form_data) == expected

    def test_cannot_get_system_nominator(self):
        form_data = {'url_value': 'http://www.example.com'}
        project = factories.ProjectFactory()
        models.Nominator.objects.get().delete()

        with pytest.raises(http.Http404):
            url_handler.add_url(project, form_data)

    @pytest.mark.xfail(reason='Unreachable path')
    def test_cannot_get_or_create_surt(self):
        form_data = {'url_value': 'http://www.example.com'}
        project = None
        with pytest.raises(http.Http404):
            url_handler.add_url(project, form_data)

    def test_cannot_get_or_create_nominator(self):
        form_data = {
            'url_value': 'http://www.example.com',
            'nominator_email': None,
            'nominator_name': None,
            'nominator_institution': None
        }
        project = factories.ProjectFactory()

        with pytest.raises(http.Http404):
            url_handler.add_url(project, form_data)


class TestAddMetadata():

    def test_returns_expected(self):
        project = factories.ProjectWithMetadataFactory()
        nominator = factories.NominatorFactory()
        attribute_name = project.metadata.first().name
        value = 'some_value'
        form_data = {
            'nominator_email': nominator.nominator_email,
            'scope': '1',
            'url_value': 'http://www.example.com',
            attribute_name: value
        }
        expected = [
            'You have successfully nominated {0}'.format(form_data['url_value']),
            'You have successfully added the {0} "{1}" for {2}'.format(
                attribute_name, value, form_data['url_value'])
        ]

        assert url_handler.add_metadata(project, form_data) == expected

    def test_nominator_not_found(self):
        project = factories.ProjectFactory()
        form_data = {'nominator_email': 'someone@someplace.com'}

        with pytest.raises(http.Http404):
            url_handler.add_metadata(project, form_data)


@pytest.mark.parametrize('url, expected', [
    ('http://www.example.com', 'http://www.example.com'),
    ('   http://www.example.com   ', 'http://www.example.com'),
    ('https://www.example.com', 'https://www.example.com'),
    ('http://www.example.com///', 'http://www.example.com')
])
def test_check_url(url, expected):
    assert url_handler.check_url(url) == expected


class TestGetNominator():

    def test_returns_nominator(self):
        nominator = factories.NominatorFactory()
        form_data = {'nominator_email': nominator.nominator_email}
        assert url_handler.get_nominator(form_data) == nominator

    def test_creates_and_returns_nominator(self):
        form_data = {
            'nominator_email': 'somebody@somewhere.com',
            'nominator_name': 'John Smith',
            'nominator_institution': 'UNT'
        }

        assert len(models.Nominator.objects.all()) == 1
        new_nominator = url_handler.get_nominator(form_data)
        assert len(models.Nominator.objects.all()) == 2
        for key in form_data.keys():
            assert getattr(new_nominator, key) == form_data[key]

    def test_cannot_create_nominator(self):
        form_data = {
            'nominator_email': 'somebody@somewhere.com',
            'nominator_name': None,
            'nominator_institution': None
        }
        new_nominator = url_handler.get_nominator(form_data)

        assert new_nominator is False


class TestNominateURL():

    @pytest.mark.parametrize('scope_value, scope', [
        ('1', 'In Scope'),
        ('0', 'Out of Scope')
    ])
    def test_nomination_exists(self, scope_value, scope):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        form_data = {'url_value': 'http://www.example.com'}
        factories.NominatedURLFactory(
            url_nominator=nominator,
            url_project=project,
            entity=form_data['url_value'],
            value=scope_value
        )
        results = url_handler.nominate_url(project, nominator, form_data, scope_value)[0]

        assert 'already' in results
        assert scope in results

    @pytest.mark.parametrize('scope_value, scope', [
        ('1', 'In Scope'),
        ('0', 'Out of Scope')
    ])
    def test_nomination_gets_modified(self, scope_value, scope):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        form_data = {'url_value': 'http://www.example.com'}
        factories.NominatedURLFactory(
            url_nominator=nominator,
            url_project=project,
            entity=form_data['url_value'],
            value='1' if scope_value == '0' else '0'
        )
        results = url_handler.nominate_url(project, nominator, form_data, scope_value)[0]

        assert 'successfully' in results
        assert scope in results

    def test_creates_new_nomination(self):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        form_data = {'url_value': 'http://www.example.com'}
        scope_value = 1
        results = url_handler.nominate_url(project, nominator, form_data, scope_value)[0]
        expected = 'You have successfully nominated {0}'.format(form_data['url_value'])

        assert results == expected

    def test_cannot_create_nomination(self):
        project = nominator = scope_value = None
        form_data = {}

        with pytest.raises(http.Http404):
            url_handler.nominate_url(project, nominator, form_data, scope_value)


class TestAddOtherAttribute():

    @pytest.fixture
    def setup(self):
        nominator = factories.NominatorFactory()
        project = factories.ProjectWithMetadataFactory()
        metadata_names = [md.name for md in project.metadata.all()]
        return project, metadata_names, nominator

    def test_returns_expected(self, setup):
        project, metadata_names, nominator = setup
        entity = 'http://www.example.com'
        value = 'some_value'

        form_data = {'url_value': entity}
        for metadata in metadata_names:
            form_data[metadata] = value

        results = url_handler.add_other_attribute(project, nominator, form_data, [])

        expected = [
            'You have successfully added the {0} "{1}" for {2}'.format(met_name, value, entity)
            for met_name in metadata_names
        ]

        assert results.sort() == expected.sort()

    def test_returns_expected_with_multiple_attribute_values(self, setup):
        project, metadata_names, nominator = setup
        entity = 'http://www.example.com'
        values = ['some_value', 'some_other_value']

        form_data = {'url_value': entity}
        for metadata in metadata_names:
            form_data[metadata] = values

        results = url_handler.add_other_attribute(project, nominator, form_data, [])
        expected = [
            'You have successfully added the {0} "{1}" for {2}'.format(met_name, value, entity)
            for met_name in metadata_names
            for value in values
        ]

        assert results.sort() == expected.sort()


class TestSaveAttribute():

    def test_creates_url(self):
        results = url_handler.save_attribute(
            factories.ProjectFactory(),
            factories.NominatorFactory(),
            {'url_value': 'http://www.example.com'},
            [],
            'Language',
            'English'
        )

        assert 'You have successfully added' in results[0]
        assert models.URL.objects.all().count() == 1

    def test_does_not_create_url_if_it_exists_already(self):
        url = factories.URLFactory()
        results = url_handler.save_attribute(
            url.url_project,
            url.url_nominator,
            {'url_value': url.entity},
            [],
            url.attribute,
            url.value
        )

        assert 'You have already added' in results[0]
        assert models.URL.objects.all().count() == 1

    def test_url_cannot_be_saved(self):
        with pytest.raises(http.Http404):
            with transaction.atomic():
                url_handler.save_attribute(None, None, {'url_value': ''}, [], '', '',)
        assert models.URL.objects.all().count() == 0


class TestSurtExists():

    def test_returns_true_with_existing_surt(self):
        system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
        url = factories.SURTFactory()
        assert url_handler.surt_exists(url.url_project, system_nominator, url.entity) is True

    def test_creates_surt_when_surt_does_not_exist(self):
        system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
        project = factories.ProjectFactory()
        url = 'http://example.com'

        assert len(models.URL.objects.all()) == 0
        assert url_handler.surt_exists(project, system_nominator, url) is True
        assert len(models.URL.objects.all()) == 1

    def test_surt_cannot_be_created(self):
        system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
        project = factories.ProjectFactory()
        url = None

        with pytest.raises(http.Http404):
            url_handler.surt_exists(project, system_nominator, url)


@pytest.mark.parametrize('url, expected', [
    ('www.example.com', 'http://www.example.com'),
    ('   http://www.example.com   ', 'http://www.example.com')
])
def test_url_formatter(url, expected):
    assert url_handler.url_formatter(url) == expected


@pytest.mark.parametrize('url, preserveCase, expected', [
    # Documentation on SURTs is inconsistent about whether a comma
    # should come before the port or not. The assumption here is
    # that it should.
    ('http://userinfo@domain.tld:80/path?query#fragment', False,
        'http://(tld,domain,:80@userinfo)/path?query#fragment'),
    ('http://www.example.com', False, 'http://(com,example,www,)'),
    ('ftp://www.example.com', False, 'ftp://(com,example,www,)'),
    ('ftps://www.example.com', False, 'ftp://(com,example,www,)'),
    ('https://www.example.com', False, 'http://(com,example,www,)'),
    ('www.example.com', False, 'http://(com,example,www,)'),
    ('http://www.eXaMple.cOm', True, 'http://(cOm,eXaMple,www,)'),
    ('Not a URL.', False, ''),
    ('1.2.3.4:80/examples', False, 'http://(1.2.3.4:80)/examples'),
])
def test_surtize(url, preserveCase, expected):
    assert url_handler.surtize(url, preserveCase=preserveCase) == expected


def test_appendToSurt():
    match_obj = re.search(r'(World!)', 'The End of The World!')
    groupnum = 1
    surt = 'Hello, '
    expected = 'Hello, World!'

    assert url_handler.appendToSurt(match_obj, groupnum, surt) == expected


@pytest.mark.parametrize('uri, expected', [
    ('http://www.example.com', 'http://www.example.com'),
    ('www.example.com', 'http://www.example.com'),
    (':.', ':.'),
    ('.:', 'http://.:')
])
def test_addImpliedHttpIfNecessary(uri, expected):
    assert url_handler.addImpliedHttpIfNecessary(uri) == expected


class TestCreateJsonBrowse():

    @pytest.mark.parametrize('root, text, id_group', [
        ('com,', '<a href="surt/(com,example">com,example</a>', 'com,example,'),
        ('', 'com', 'com,')
    ])
    def test_returns_expected(self, root, text, id_group):
        project = factories.ProjectFactory()
        factories.SURTFactory(
            url_project=project,
            entity='http://www.example.com',
            value='http://(com,example,www)'
        )
        expected = [{
            'hasChildren': True,
            'id': id_group,
            'text': text
        }]
        results = url_handler.create_json_browse(project.project_slug, None, root)

        assert json.loads(results) == expected

    @pytest.mark.parametrize('root, text, id_group', [
        ('com,', '<a href="surt/(com,example">com,example</a>', 'com,example,'),
        ('', 'com', 'com,')
    ])
    def test_handles_non_http(self, root, text, id_group):
        project = factories.ProjectFactory()
        factories.SURTFactory(
            url_project=project,
            entity='ftp://www.example.com',
            value='ftp://(com,example,www)'
        )
        expected = [{
            'hasChildren': True,
            'id': id_group,
            'text': text
        }]
        results = url_handler.create_json_browse(project.project_slug, None, root)

        assert json.loads(results) == expected

    def test_returns_expected_with_no_children(self):
        project = factories.ProjectFactory()
        factories.SURTFactory(
            url_project=project,
            entity='http://www.example.com',
            value='http://(com,example,www)'
        )
        root = 'com,example,'
        expected = [{
            'id': 'com,example,www,',
            'text': '<a href="surt/(com,example,www">com,example,www</a>'
        }]
        results = url_handler.create_json_browse(project.project_slug, None, root)

        assert json.loads(results) == expected

    @pytest.mark.parametrize('root, text, id_group', [
        ('com,', '<a href="surt/(com,example">com,example</a>', 'com,example,'),
        ('', 'com', 'com,'),
    ])
    def test_does_not_show_duplicates(self, root, text, id_group):
        project = factories.ProjectFactory()
        factories.SURTFactory.create_batch(
            2,
            url_project=project,
            entity='http://www.example.com',
            value='http://(com,example,www)'
        )
        factories.SURTFactory(
            url_project=project,
            entity='ftp://www.example.com',
            value='ftp://(com,example,www)'
        )
        expected = [{
            'hasChildren': True,
            'id': id_group,
            'text': text
        }]
        results = url_handler.create_json_browse(project.project_slug, None, root)

        assert json.loads(results) == expected

    def test_groups_by_prefix_when_many_urls_exist(self):
        project = factories.ProjectFactory()
        urls = factories.SURTFactory.create_batch(101, url_project=project)
        root = 'com,'
        results = url_handler.create_json_browse(project.project_slug, None, root)

        expected = [
            {
                'hasChildren': True,
                'id': root + url.value[url.value.find(root) + 4],
                'text': url.value[url.value.find(root) + 4]
            } for url in urls
        ]

        for result in json.loads(results):
            assert result in expected

        # assert json.loads(results).sort() == expected.sort()

    def test_cannot_find_project(self):
        slug = 'blah'
        with pytest.raises(http.Http404):
            url_handler.create_json_browse(slug, None, None)

    def test_cannot_find_matching_surts(self):
        project = factories.ProjectFactory()
        root = 'example'
        assert url_handler.create_json_browse(project.project_slug, None, root) == '[]'

    def test_empty_root(self):
        project = factories.ProjectFactory()
        root = ''
        assert url_handler.create_json_browse(project.project_slug, None, root) == '[]'


class TestCreateJsonSearch():

    def test_returns_expected(self):
        project = factories.ProjectFactory()
        expected_urls = factories.URLFactory.create_batch(10, url_project=project)
        other_urls = factories.URLFactory.create_batch(10)
        json_url_list = url_handler.create_json_search(project.project_slug)

        for url in expected_urls:
            assert url.entity in json_url_list

        for url in other_urls:
            assert url.entity not in json_url_list

    def test_project_not_found(self):
        with pytest.raises(http.Http404):
            url_handler.create_json_search('fake_slug')


class TestCreateURLList():

    def test_returns_expected(self):
        project = factories.ProjectFactory()
        entity = 'www.example.com'
        surt = 'http://(com,example,www,)'
        domain_surt = 'http://(com,example,'
        urls = factories.URLFactory.create_batch(5, url_project=project, entity=entity)
        nominations = factories.NominatedURLFactory.create_batch(
            5,
            url_project=project,
            entity=entity
        )
        score = 0
        for nomination in nominations:
            score += int(nomination.value)
        factories.SURTFactory(url_project=project, entity=entity, value=surt)
        results = url_handler.create_url_list(
            project,
            models.URL.objects.filter(entity__iexact=entity)
        )

        assert results['entity'] == entity
        for nomination in nominations:
            name = nomination.url_nominator.nominator_name
            institution = nomination.url_nominator.nominator_institution
            assert '{0} - {1}'.format(name, institution) in results['nomination_list']
        assert results['nomination_count'] == 5
        assert results['nomination_score'] == score
        assert results['surt'] == domain_surt
        for url in urls:
            attribute = capwords(url.attribute.replace('_', ' '))
            assert url.value in results['attribute_dict'][attribute]

    def test_returns_expected_with_project_metadata_values(self):
        project = factories.ProjectFactory()
        metadata = factories.MetadataFactory()
        factories.ProjectMetadataFactory(project=project, metadata=metadata)
        value = 'one'
        met_value = factories.MetadataValuesFactory(metadata=metadata, value__key=value).value
        url = factories.URLFactory(url_project=project, attribute=metadata.name, value=value)
        results = url_handler.create_url_list(project, [url])
        attribute = capwords(url.attribute.replace('_', ' '))

        assert results['attribute_dict'][attribute] == [met_value]


class TestCreateURLDump():

    def test_returns_expected_with_nomination(self):
        project = factories.ProjectFactory()
        url = factories.NominatedURLFactory(url_project=project)
        nominator = url.url_nominator
        results = url_handler.create_url_dump(project)

        assert results == {
            url.entity: {
                'nominators': ['{0} - {1}'.format(
                    nominator.nominator_name,
                    nominator.nominator_institution
                )],
                'nomination_count': 1,
                'nomination_score': int(url.value),
                'attributes': {}
            }
        }

    def test_returns_expected_with_surt(self):
        project = factories.ProjectFactory()
        surt = 'http://(com,example,www)'
        domain_surt = 'http://(com,example,'
        url = factories.SURTFactory(url_project=project, value=surt)
        results = url_handler.create_url_dump(project)

        assert results == {
            url.entity: {
                'nominators': [],
                'nomination_count': 0,
                'nomination_score': 0,
                'attributes': {},
                'surt': surt,
                'domain_surt': domain_surt
            }
        }

    def test_returns_correct_attribute(self):
        project = factories.ProjectWithMetadataFactory(metadata2=None)
        attribute = project.metadata.all()[0].name
        value = models.Metadata_Values.objects.filter(metadata__name__iexact=attribute)[0].value
        url = factories.URLFactory(url_project=project, attribute=attribute, value=value.key)
        results = url_handler.create_url_dump(project)

        assert results == {
            url.entity: {
                'nominators': [],
                'nomination_count': 0,
                'nomination_score': 0,
                'attributes': {attribute: [value.value]},
            }
        }

    def test_returns_correct_attribute_with_new_value(self):
        project = factories.ProjectWithMetadataFactory(metadata2=None)
        attribute = project.metadata.all()[0].name
        url = factories.URLFactory(url_project=project, attribute=attribute)
        results = url_handler.create_url_dump(project)

        assert results == {
            url.entity: {
                'nominators': [],
                'nomination_count': 0,
                'nomination_score': 0,
                'attributes': {attribute: [url.value]},
            }
        }


class TestCreateSurtDict():

    @pytest.mark.parametrize('surt_root, expected_letter', [
        ('http://(com,example,www,)', False),
        ('http://(com,a,', 'a')
    ])
    def test_returns_expected(self, surt_root, expected_letter):
        project = factories.ProjectFactory()
        surts = [
            surt_root + '/some/stuff',
            surt_root + '/other/stuff',
            surt_root + '/nothing',
            surt_root
        ]
        urls = [factories.SURTFactory(url_project=project, value=surt) for surt in surts]
        surt_dict = url_handler.create_surt_dict(project, surt_root)

        assert len(surt_dict['url_list']) == len(surts)
        for url in surt_dict['url_list']:
            assert url in urls
        assert surt_dict['letter'] == expected_letter

    def test_returns_none_when_no_surts_found(self):
        surt_dict = url_handler.create_surt_dict('', 'http://(com,example,)')
        assert surt_dict['url_list'] is None


@pytest.mark.parametrize('surt, expected', [
    ('http://(com,example,www,)', 'http://(com,example,'),
    ('http://(uk,gov,nationalarchives,www,)', 'http://(uk,gov,'),
    ('http://not-a-surt.com', 'http://not-a-surt.com')
])
def test_get_domain_surt(surt, expected):
    assert url_handler.get_domain_surt(surt) == expected


def test_fix_scheme_double_slash():
    url = 'http:/www.example.com'
    expected = 'http://www.example.com'
    assert url_handler.fix_scheme_double_slash(url) == expected


def test_fix_scheme_double_slash_ftp():
    url = 'ftp:/www.example.com/clvl37.idx'
    expected = 'ftp://www.example.com/clvl37.idx'
    assert url_handler.fix_scheme_double_slash(url) == expected


def test_strip_scheme():
    url = 'https://example.com'
    expected = 'example.com'
    assert url_handler.strip_scheme(url) == expected
