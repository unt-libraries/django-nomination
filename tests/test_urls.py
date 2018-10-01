from django.urls import resolve

from nomination import views


def test_project_listing():
    url = '/nomination/'
    assert resolve(url).func == views.project_listing


def test_robot_ban():
    url = '/nomination/robots.txt'
    assert resolve(url).func == views.robot_ban


def test_nomination_about():
    url = '/nomination/about/'
    assert resolve(url).func == views.nomination_about


def test_nomination_help():
    url = '/nomination/help/'
    assert resolve(url).func == views.nomination_help


def test_url_lookup():
    url = '/nomination/some_project/lookup/'
    assert resolve(url).func == views.url_lookup


def test_search_json():
    url = '/nomination/some_project/search.json'
    assert resolve(url).func == views.search_json


def test_browse_json():
    url = '/nomination/some_project/browse/some_attribute/browse.json'
    assert resolve(url).func == views.browse_json


def test_project_dump():
    url = '/nomination/some_project/reports/projectdump/'
    assert resolve(url).func == views.project_dump


def test_url_score_report():
    url = '/nomination/some_project/reports/urls/score/'
    assert resolve(url).func == views.url_score_report


def test_url_nomination_report():
    url = '/nomination/some_project/reports/urls/nomination/'
    assert resolve(url).func == views.url_nomination_report


def test_url_date_report():
    url = '/nomination/some_project/reports/urls/date/'
    assert resolve(url).func == views.url_date_report


def test_url_report():
    url = '/nomination/some_project/reports/urls/'
    assert resolve(url).func == views.url_report


def test_surt_report():
    url = '/nomination/some_project/reports/surts/'
    assert resolve(url).func == views.surt_report


def test_nominator_report_using_nominator():
    url = '/nomination/some_project/reports/metadata/nominator/'
    assert resolve(url).func == views.nominator_report


def test_nominator_report_using_institution():
    url = '/nomination/some_project/reports/metadata/institution/'
    assert resolve(url).func == views.nominator_report


def test_nominator_url_report_using_nominator():
    url = '/nomination/some_project/reports/metadata/nominator/12/'
    assert resolve(url).func == views.nominator_url_report


def test_nominator_url_report_using_institution():
    url = '/nomination/some_project/reports/metadata/institution/12/'
    assert resolve(url).func == views.nominator_url_report


def test_field_report():
    url = '/nomination/some_project/reports/metadata/some_metadata/'
    assert resolve(url).func == views.field_report


def test_value_report():
    url = '/nomination/some_project/reports/metadata/some_metadata/some_value/'
    assert resolve(url).func == views.value_report


def test_reports_view():
    url = '/nomination/some_project/reports/'
    assert resolve(url).func == views.reports_view


def test_url_listing():
    url = '/nomination/some_project/url/some_url/'
    assert resolve(url).func == views.url_listing


def test_url_listing_reports_clash():
    """Test that a URL ending in '/reports/' uses the correct view."""
    url = '/nomination/some_project/url/some_url/reports/'
    assert resolve(url).func == views.url_listing


def test_url_surt():
    url = '/nomination/some_project/surt/some_surt/'
    assert resolve(url).func == views.url_surt


def test_url_add():
    url = '/nomination/some_project/add/'
    assert resolve(url).func == views.url_add


def test_project_about():
    url = '/nomination/some_project/about/'
    assert resolve(url).func == views.project_about


def test_nomination_feed():
    url = '/nomination/some_project/feed/nominations/'
    assert resolve(url).view_name == 'nomination_feed'


def test_url_feed():
    url = '/nomination/some_project/feed/urls/'
    assert resolve(url).view_name == 'url_feed'


def test_project_urls():
    url = '/nomination/some_project/'
    assert resolve(url).func == views.project_urls
