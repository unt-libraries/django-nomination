import re
import json
from string import digits, uppercase, capwords

from django import http
from django.conf import settings

import pytest

from nomination import url_handler, models
import factories


pytestmark = pytest.mark.django_db
alnum_list = sorted(digits + uppercase)


def test_alphabetical_browse():
    surts = {
        'A': ('http://(org,alarm,)', 'http://(org,a'),
        'C': ('http://(org,charlie,)', 'http://(org,c'),
        '1': ('http://(org,123,)', 'http://(org,1')
    }
    project = factories.ProjectFactory()
    # Create the surts we're expecting to see represented in the returned dict.
    [factories.SURTFactory(url_project=project, value=surts[key][0]) for key in iter(surts)]
    expected = {'org': [(x, surts[x][1] if surts.get(x) else None) for x in alnum_list]}
    # Create another unrelated SURT to make sure we aren't grabbing everything.
    factories.SURTFactory()
    returned = url_handler.alphabetical_browse(project)

    assert returned == expected


@pytest.mark.parametrize('surt, expected', [
    ('http://(,)', {}),
    ('http://(org,)', {'org': [(x, None) for x in alnum_list]})
])
def test_alphabetical_browse_domains_not_found(surt, expected):
    project = factories.ProjectFactory()
    factories.SURTFactory(url_project=project, value=surt)
    returned = url_handler.alphabetical_browse(project)

    assert returned == expected


def test_alphabetical_browse_fake_project():
    project = 'not a real project'
    with pytest.raises(http.Http404):
        url_handler.alphabetical_browse(project)


def test_get_metadata():
    project = factories.ProjectFactory()
    vals = [x.metadata for x in factories.MetadataValuesFactory.create_batch(3)]
    metadata = [factories.ProjectMetadataFactory(project=project, metadata=x) for x in vals]
    expected = [(x, [models.Metadata_Values.objects.get(metadata=x).value]) for x in metadata]
    returned = url_handler.get_metadata(project)

    for each in returned:
        assert str(each) in str(expected)


def test_get_metadata_with_valueset():
    project = factories.ProjectFactory()
    valset = factories.ValuesetFactory()
    vals = [factories.ValuesetValuesFactory(valueset=valset).value for i in range(3)]
    metadata = factories.MetadataFactory(value_sets=[valset])
    factories.ProjectMetadataFactory(project=project, metadata=metadata)
    returned = url_handler.get_metadata(project)

    for _, value_iter in returned:
        for value in value_iter:
            assert value in vals


def test_handle_metadata(rf):
    request = rf.post(
        '/',
        {
            'color': ['blue', 'other_specify'],
            'group': ['alpha', 'other_specify'],
            'name': ['Dan', 'Sara'],
            'title': ['other_specify'],
            'job': ['other_specify'],
        }
    )
    posted_data = {
        'color': ['blue', 'other_specify'],
        'color_other': 'magenta',
        'group': ['alpha', 'other_specify'],
        'name': ['Dan', 'Sara'],
        'title': 'other_specify',
        'title_other': 'Monsieur',
        'job': 'other_specify',
    }
    expected = {
        'color': ['blue', 'magenta'],
        'color_other': 'magenta',
        'group': ['alpha'],
        'name': ['Dan', 'Sara'],
        'title': 'Monsieur',
        'title_other': 'Monsieur',
        # Is this really what we want returned if the 'other' attribute isn't set?
        'job': 'other_specify',
    }

    assert url_handler.handle_metadata(request, posted_data) == expected


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
def test_validate_date_with_valid_dates(date_str):
    assert url_handler.validate_date(date_str) is not None


def test_validate_date_with_invalid_date():
    date_str = '2006, Oct 25'
    assert url_handler.validate_date(date_str) is None


def test_add_url():
    project, metadata = factories.project_with_metadata()
    attribute_names = [x.name for x in metadata]
    value = 'some_value'
    form_data = {
        'url_value': 'http://www.example.com',
        'nominator_email': 'somebody@someplace.com',
        'nominator_name': 'John Lambda',
        'nominator_institution': 'UNT',
        attribute_names[0]: value
    }
    expected = [
        'You have successfully nominated {0}'.format(form_data['url_value']),
        'You have successfully added the {0} "{1}" for {2}'.format(
            attribute_names[0], value, form_data['url_value'])
    ]

    for each in url_handler.add_url(project, form_data):
        assert each in expected


def test_add_url_cannot_get_system_nominator():
    form_data = {'url_value': 'http://www.example.com'}
    project = factories.ProjectFactory()
    models.Nominator.objects.get().delete()

    with pytest.raises(http.Http404):
        url_handler.add_url(project, form_data)


@pytest.mark.xfail(reason='Called function surt_exists raises 404, does not return Falsy value.')
def test_add_url_cannot_get_or_create_surt():
    form_data = {'url_value': 'http://www.example.com'}
    project = None
    with pytest.raises(http.Http404):
        url_handler.add_url(project, form_data)


def test_add_url_cannot_get_or_create_nominator():
    form_data = {
        'url_value': 'http://www.example.com',
        'nominator_email': None,
        'nominator_name': None,
        'nominator_institution': None
    }
    project = factories.ProjectFactory()

    with pytest.raises(http.Http404):
        url_handler.add_url(project, form_data)


def test_add_metadata():
    project, metadata = factories.project_with_metadata()
    nominator = factories.NominatorFactory()
    attribute_names = [x.name for x in metadata]
    value = 'some_value'
    form_data = {
        'nominator_email': nominator.nominator_email,
        'scope': '1',
        'url_value': 'http://www.example.com',
        attribute_names[0]: value
    }
    expected = [
        'You have successfully nominated {0}'.format(form_data['url_value']),
        'You have successfully added the {0} "{1}" for {2}'.format(
            attribute_names[0], value, form_data['url_value'])
    ]

    for each in url_handler.add_metadata(project, form_data):
        assert each in expected


def test_add_metadata_nominator_does_not_exist_in_project():
    project = factories.ProjectFactory()
    form_data = {'nominator_email': 'someone@someplace.com'}

    with pytest.raises(http.Http404):
        url_handler.add_metadata(project, form_data)


@pytest.mark.parametrize('url, expected', [
    ('http://www.example.com', 'http://www.example.com'),
    ('   http://www.example.com   ', 'http://www.example.com'),
    ('https://www.example.com', 'http://www.example.com'),
    ('http://http://www.example.com', 'http://www.example.com'),
    ('http://www.example.com///', 'http://www.example.com')
])
def test_check_url(url, expected):
    assert url_handler.check_url(url) == expected


def test_get_nominator_when_nominator_exists():
    nominator = factories.NominatorFactory()
    form_data = {'nominator_email': nominator.nominator_email}
    assert url_handler.get_nominator(form_data) == nominator


def test_get_nominator_when_nominator_does_not_exist():
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


def test_get_nominator_when_nominator_cannot_be_created():
    form_data = {
        'nominator_email': 'somebody@somewhere.com',
        'nominator_name': None,
        'nominator_institution': None
    }
    new_nominator = url_handler.get_nominator(form_data)

    assert new_nominator is False


@pytest.mark.parametrize('scope_value, expected', [
    ('1', 'You have already declared {} as "In Scope"'),
    ('0', 'You have already declared {} as "Out of Scope"')
])
def test_nominate_url_nomination_exists(scope_value, expected):
    project = factories.ProjectFactory()
    nominator = factories.NominatorFactory()
    form_data = {'url_value': 'http://www.example.com'}
    factories.NominatedURLFactory(
        url_nominator=nominator,
        url_project=project,
        entity=form_data['url_value'],
        value=scope_value
    )

    assert (url_handler.nominate_url(project, nominator, form_data, scope_value) ==
            [expected.format(form_data['url_value'])])


@pytest.mark.parametrize('scope_value, expected', [
    ('1', 'You have successfully declared {} as "In Scope"'),
    ('0', 'You have successfully declared {} as "Out of Scope"')
])
def test_nominate_url_nomination_modified(scope_value, expected):
    project = factories.ProjectFactory()
    nominator = factories.NominatorFactory()
    form_data = {'url_value': 'http://www.example.com'}
    factories.NominatedURLFactory(
        url_nominator=nominator,
        url_project=project,
        entity=form_data['url_value'],
        value='1' if scope_value == '0' else '0'
    )

    assert (url_handler.nominate_url(project, nominator, form_data, scope_value) ==
            [expected.format(form_data['url_value'])])


def test_nominate_url_new_nomination():
    project = factories.ProjectFactory()
    nominator = factories.NominatorFactory()
    form_data = {'url_value': 'http://www.example.com'}
    scope_value = 1
    expected = ['You have successfully nominated {0}'.format(form_data['url_value'])]

    assert url_handler.nominate_url(project, nominator, form_data, scope_value) == expected


def test_nominate_url_cannot_create_nomination():
    project = None
    nominator = None
    form_data = {}
    scope_value = None

    with pytest.raises(http.Http404):
        url_handler.nominate_url(project, nominator, form_data, scope_value)


@pytest.mark.parametrize('attr_value', [
    ['some_value', ],
    ['some_value', 'some_other_value']
])
def test_add_other_attribute(attr_value):
    nominator = factories.NominatorFactory()
    project, metadata = factories.project_with_metadata()
    form_data = {'url_value': 'http://www.example.com'}
    expected = []
    for metadata_att in [x.name for x in metadata]:
        form_data[metadata_att] = attr_value if len(attr_value) > 1 else attr_value[0]
        for value in attr_value:
            expected.append('You have successfully added the {0} "{1}" for {2}'.format(
                metadata_att, value, form_data['url_value']))
    summary_list = []
    returned = url_handler.add_other_attribute(project, nominator, form_data, summary_list)

    for each in returned:
        assert each in expected


def test_save_attribute():
    returned = url_handler.save_attribute(
        factories.ProjectFactory(),
        factories.NominatorFactory(),
        {'url_value': 'http://www.example.com'},
        [],
        'Language',
        'English'
    )

    assert 'You have successfully added' in returned[0]
    assert models.URL.objects.all().count() == 1


@pytest.mark.xfail(reason='Search for existing URL object with same atts is broken.')
def test_save_attribute_url_with_attribute_already_exists():
    url = factories.URLFactory()
    returned = url_handler.save_attribute(
        url.url_project,
        url.url_nominator,
        {'url_value': url.entity},
        [],
        url.attribute,
        url.value
    )

    assert 'You have already added' in returned[0]
    assert models.URL.objects.all().count() == 1


def test_save_attribute_url_with_attribute_cannot_be_saved():
    with pytest.raises(http.Http404):
        url_handler.save_attribute(None, None, {'url_value': ''}, [], '', '',)
    assert models.URL.objects.all().count() == 0


def test_surt_exists_when_surt_exists():
    system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
    url = factories.SURTFactory()
    assert url_handler.surt_exists(url.url_project, system_nominator, url.entity) is True


def test_surt_exists_when_surt_does_not_exist():
    system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
    project = factories.ProjectFactory()
    url = 'http://example.com'

    assert len(models.URL.objects.all()) == 0
    assert url_handler.surt_exists(project, system_nominator, url) is True
    assert len(models.URL.objects.all()) == 1


def test_surt_exists_when_surt_cannot_be_created():
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
    # Documentation on SURTs is incosistent about whether comma
    # should come before the port or not. The assumption here is
    # that it should.
    ('http://userinfo@domain.tld:80/path?query#fragment', False,
        'http://(tld,domain,:80@userinfo)/path?query#fragment'),
    ('http://www.example.com', False, 'http://(com,example,www,)'),
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


@pytest.mark.parametrize('root, text, id', [
    ('com,', '<a href="surt/http://(com,example">com,example</a>', 'com,example,'),
    ('', 'com', 'com,')
])
def test_create_json_browse(root, text, id):
    project = factories.ProjectFactory()
    factories.SURTFactory(
        url_project=project,
        entity='http://www.example.com',
        value='http://(com,example,www)'
    )
    expected = [{
        'hasChildren': True,
        'id': id,
        'text': text
    }]
    returned = url_handler.create_json_browse(project.project_slug, None, root)

    assert json.loads(returned) == expected


def test_create_json_browse_no_children():
    project = factories.ProjectFactory()
    factories.SURTFactory(
        url_project=project,
        entity='http://www.example.com',
        value='http://(com,example,www)'
    )
    root = 'com,example,'
    expected = [{
        'id': 'com,example,www,',
        'text': '<a href="surt/http://(com,example,www">com,example,www</a>'
    }]
    returned = url_handler.create_json_browse(project.project_slug, None, root)

    assert json.loads(returned) == expected


@pytest.mark.parametrize('root, text, id', [
    ('com,', '<a href="surt/http://(com,example">com,example</a>', 'com,example,'),
    ('', 'com', 'com,'),
])
def test_create_json_browse_does_not_show_duplicates(root, text, id):
    project = factories.ProjectFactory()
    factories.SURTFactory.create_batch(
        2,
        url_project=project,
        entity='http://www.example.com',
        value='http://(com,example,www)'
    )
    expected = [{
        'hasChildren': True,
        'id': id,
        'text': text
    }]
    returned = url_handler.create_json_browse(project.project_slug, None, root)

    assert json.loads(returned) == expected


def test_create_json_browse_valid_root_many_urls():
    project = factories.ProjectFactory()
    urls = factories.SURTFactory.create_batch(101, url_project=project)
    root = 'com,'
    returned = url_handler.create_json_browse(project.project_slug, None, root)
    expected = [
        {
            'hasChildren': True,
            'id': root + x.value[x.value.find(root) + 4],
            'text': x.value[x.value.find(root) + 4]
        } for x in urls
    ]

    for each in json.loads(returned):
        assert each in expected


def test_create_json_browse_project_does_not_exist():
    slug = 'blah'
    with pytest.raises(http.Http404):
        url_handler.create_json_browse(slug, None, None)


def test_create_json_browse_valid_root_without_matching_surt():
    project = factories.ProjectFactory()
    root = 'example'
    assert url_handler.create_json_browse(project.project_slug, None, root) == '[]'


def test_create_json_browse_empty_root_without_surt():
    project = factories.ProjectFactory()
    root = ''
    assert url_handler.create_json_browse(project.project_slug, None, root) == '[]'


@pytest.mark.xfail(reason='URLs are not being filtered by project.')
def test_create_json_search_project_found():
    project = factories.ProjectFactory()
    expected_urls = factories.URLFactory.create_batch(10, url_project=project)
    other_urls = factories.URLFactory.create_batch(10)
    json_url_list = url_handler.create_json_search(project.project_slug)

    for url in expected_urls:
        assert url.entity in json_url_list

    for url in other_urls:
        assert url.entity not in json_url_list


def test_create_json_search_project_not_found():
    with pytest.raises(http.Http404):
        url_handler.create_json_search('fake_slug')


def test_create_url_list():
    project = factories.ProjectFactory()
    url = 'www.example.com'
    surt = 'http://(com,example,www,)'
    domain_surt = 'http://(com,example,'
    rand_metadata = factories.URLFactory.create_batch(5, url_project=project, entity=url)
    nominations = factories.NominatedURLFactory.create_batch(5, url_project=project, entity=url)
    score = 0
    for nomination in nominations:
        score += int(nomination.value)
    factories.SURTFactory(url_project=project, entity=url, value=surt)
    returned = url_handler.create_url_list(project, models.URL.objects.filter(entity__iexact=url))

    assert returned['entity'] == url
    for each in nominations:
        assert '{0} - {1}'.format(
            each.url_nominator.nominator_name,
            each.url_nominator.nominator_institution
        ) in returned['nomination_list']
    assert returned['nomination_count'] == 5
    assert returned['nomination_score'] == score
    assert returned['surt'] == domain_surt
    for each in rand_metadata:
        assert each.value in returned['attribute_dict'][capwords(each.attribute.replace('_', ' '))]


def test_create_url_list_with_associated_project_metadata_values():
    project = factories.ProjectFactory()
    metadata = factories.MetadataFactory()
    factories.ProjectMetadataFactory(project=project, metadata=metadata)
    value = 'one'
    met_value = factories.MetadataValuesFactory(metadata=metadata, value__key=value).value
    url = factories.URLFactory(url_project=project, attribute=metadata.name, value=value)
    returned = url_handler.create_url_list(project, [url])

    assert returned['attribute_dict'][capwords(url.attribute.replace('_', ' '))] == [met_value]


def test_create_url_dump_url_nomination():
    project = factories.ProjectFactory()
    url = factories.NominatedURLFactory(url_project=project)
    nominator = url.url_nominator
    returned = url_handler.create_url_dump(project)

    assert returned == {
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


def test_create_url_dump_url_surt():
    project = factories.ProjectFactory()
    surt = 'http://(com,example,www)'
    domain_surt = 'http://(com,example,'
    url = factories.SURTFactory(url_project=project, value=surt)
    returned = url_handler.create_url_dump(project)

    assert returned == {
        url.entity: {
            'nominators': [],
            'nomination_count': 0,
            'nomination_score': 0,
            'attributes': {},
            'surt': surt,
            'domain_surt': domain_surt
        }
    }


def test_create_url_dump_url_attribute():
    project, metadata = factories.project_with_metadata()
    attribute = metadata[0].name
    value = models.Metadata_Values.objects.filter(metadata__name__iexact=attribute)[0].value
    url = factories.URLFactory(url_project=project, attribute=attribute, value=value.key)
    returned = url_handler.create_url_dump(project)

    assert returned == {
        url.entity: {
            'nominators': [],
            'nomination_count': 0,
            'nomination_score': 0,
            'attributes': {attribute: [value.value]},
        }
    }


def test_create_url_dump_url_attribute_new_value():
    project, metadata = factories.project_with_metadata()
    attribute = metadata[0].name
    url = factories.URLFactory(url_project=project, attribute=attribute)
    returned = url_handler.create_url_dump(project)

    assert returned == {
        url.entity: {
            'nominators': [],
            'nomination_count': 0,
            'nomination_score': 0,
            'attributes': {attribute: [url.value]},
        }
    }


@pytest.mark.parametrize('surt_root, expected_letter', [
    ('http://(com,example,www,)', False),
    ('http://(com,a,', 'a')
])
def test_create_surt_dict(surt_root, expected_letter):
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


def test_create_surt_dict_exception_caught():
    surt_dict = url_handler.create_surt_dict('', 'http://(com,example,)')
    assert surt_dict['url_list'] is None


@pytest.mark.parametrize('surt, expected', [
    ('http://(com,example,www,)', 'http://(com,example,'),
    ('http://(uk,gov,nationalarchives,www,)', 'http://(uk,gov,'),
    ('http://not-a-surt.com', 'http://not-a-surt.com')
])
def test_get_domain_surt(surt, expected):
    assert url_handler.get_domain_surt(surt) == expected


def test_fix_http_double_slash():
    url = 'http:/www.example.com'
    expected = 'http://www.example.com'
    assert url_handler.fix_http_double_slash(url) == expected
