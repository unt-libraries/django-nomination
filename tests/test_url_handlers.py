import re
from string import digits, uppercase, capwords
import itertools

from django import http
from django.conf import settings

import pytest

from nomination import url_handler, models
import factories


pytestmark = pytest.mark.django_db
alnum_list = sorted(digits + uppercase)


def test_alphabetical_browse():
    surts = {
        'A': ('http://(org,alpha,)', 'http://(org,a'),
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


@pytest.mark.parametrize(
    'surt,expected',
    [
        ('http://(,)', {}),
        ('http://(org,)', {'org': [(x, None) for x in alnum_list]})
    ]
)
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
    pass


def test_get_metadata_with_valueset():
    pass


def test_handle_metadata():
    pass


@pytest.mark.parametrize(
    'date_str',
    [
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
    ]
)
def test_validate_date_with_valid_dates(date_str):
    assert url_handler.validate_date(date_str) is not None


def test_validate_date_with_invalid_date():
    date_str = '2006, Oct 25'
    assert url_handler.validate_date(date_str) is None


def test_add_url():
    pass


def test_add_metadata():
    pass


@pytest.mark.parametrize(
    'url,expected',
    [
        ('http://www.example.com', 'http://www.example.com'),
        ('   http://www.example.com   ', 'http://www.example.com'),
        ('https://www.example.com', 'http://www.example.com'),
        ('http://http://www.example.com', 'http://www.example.com'),
        ('http://www.example.com///', 'http://www.example.com')
    ]
)
def test_check_url(url, expected):
    assert url_handler.check_url(url) == expected


def test_get_nominator_when_nominator_exists():
    nominator = factories.NominatorFactory()
    form_data = {'nominator_email': nominator.nominator_email}
    assert url_handler.get_nominator(form_data) == nominator


def test_get_nominator_when_nominator_does_not_exist():
    form_data = {
        'nominator_email': 'somebody@some_email.com',
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
        'nominator_email': 'somebody@some_email.com',
        'nominator_name': None,
        'nominator_institution': None
    }
    new_nominator = url_handler.get_nominator(form_data)

    assert new_nominator is False


def test_nominate_url():
    pass


def test_add_other_attribute():
    pass


def test_add_other_attribute_with_no_attributes():
    pass


def test_add_other_attribute_with_several_attributes():
    pass


def test_save_attribute():
    returned = url_handler.save_attribute(
        factories.ProjectFactory(),
        factories.NominatorFactory(),
        {'url_value': 'www.example.com'},
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


@pytest.mark.parametrize(
    'url,expected',
    [
        ('www.example.com', 'http://www.example.com'),
        ('   http://www.example.com   ', 'http://www.example.com')
    ]
)
def test_url_formatter(url, expected):
    assert url_handler.url_formatter(url) == expected


@pytest.mark.parametrize(
    'url,preserveCase,expected',
    [
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
    ]
)
def test_surtize(url, preserveCase, expected):
    assert url_handler.surtize(url, preserveCase=preserveCase) == expected


def test_appendToSurt():
    match_obj = re.search(r'(World!)', 'The End of The World!')
    groupnum = 1
    surt = 'Hello, '
    expected = 'Hello, World!'

    assert url_handler.appendToSurt(match_obj, groupnum, surt) == expected


@pytest.mark.parametrize(
    'uri,expected',
    [
        ('http://www.example.com', 'http://www.example.com'),
        ('www.example.com', 'http://www.example.com'),
        (':.', ':.'),
        ('.:', 'http://.:')
    ]
)
def test_addImpliedHttpIfNecessary(uri, expected):
    assert url_handler.addImpliedHttpIfNecessary(uri) == expected


def test_create_json_browse():
    pass


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


def test_create_url_dump():
    pass


@pytest.mark.parametrize(
    'surt_root,expected_letter',
    [
        ('http://(com,example,www,)', False),
        ('http://(com,a,', 'a')
    ]
)
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


@pytest.mark.parametrize(
    'surt,expected',
    [
        ('http://(com,example,www,)', 'http://(com,example,'),
        ('http://(uk,gov,nationalarchives,www,)', 'http://(uk,gov,'),
        ('http://not-a-surt.com', 'http://not-a-surt.com')
    ]
)
def test_get_domain_surt(surt, expected):
    assert url_handler.get_domain_surt(surt) == expected


def test_fix_http_double_slash():
    url = 'http:/www.example.com'
    expected = 'http://www.example.com'
    assert url_handler.fix_http_double_slash(url) == expected
