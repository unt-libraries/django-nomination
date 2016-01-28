import re

from django import http
from django.conf import settings

import pytest

from nomination import url_handler, models
import factories


pytestmark = pytest.mark.django_db


def test_alphabetical_browse():
    pass


def test_alphabetical_browse_fake_project():
    project = 'not a real project'
    with pytest.raises(http.Http404):
        url_handler.alphabetical_browse(project)


def test_get_metadata():
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
    form_data = {'nominator_email':nominator.nominator_email}

    assert url_handler.get_nominator(form_data) == nominator


def test_get_nominator_when_nominator_does_not_exist():
    form_data = {
        'nominator_email':'somebody@some_email.com',
        'nominator_name':'John Smith',
        'nominator_institution':'UNT'
    }

    assert len(models.Nominator.objects.all()) == 1
    new_nominator = url_handler.get_nominator(form_data)
    assert len(models.Nominator.objects.all()) == 2
    for key in form_data.keys():
        assert getattr(new_nominator, key) == form_data[key]


def test_get_nominator_when_nominator_cannot_be_created():
    form_data = {
        'nominator_email':'somebody@some_email.com',
        'nominator_name':None,
        'nominator_institution':None
    }

    new_nominator = url_handler.get_nominator(form_data)
    assert new_nominator == False


def test_nominate_url():
    pass


def test_add_other_attribute():
    pass


def test_save_attribute():
    pass


def test_surt_exists_when_surt_exists():
    system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
    url = factories.URLFactory(attribute='surt')

    assert url_handler.surt_exists(url.url_project, system_nominator, url.entity) == True


def test_surt_exists_when_surt_does_not_exist():
    system_nominator = models.Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
    project = factories.ProjectFactory()
    url = 'http://example.com'

    assert len(models.URL.objects.all()) == 0
    assert url_handler.surt_exists(project, system_nominator, url) == True
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


def test_surtize():
    pass


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
    pass


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
    urls = [factories.URLFactory(url_project=project, attribute='surt', value=surt) for surt in surts]

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
