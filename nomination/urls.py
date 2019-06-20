from django.conf.urls import url
from nomination.views import (
    project_listing, robot_ban, nomination_about, nomination_help, url_lookup, search_json,
    browse_json, project_dump, url_score_report, url_nomination_report, url_date_report,
    url_report, surt_report, nominator_report, nominator_url_report, field_report, value_report,
    reports_view, url_listing, url_surt, url_add, project_about, project_urls
)
from nomination.feeds import url_feed, nomination_feed

urlpatterns = [
    url(r"^$", project_listing, name='project_listing'),
    url(r"^robots.txt$", robot_ban, name='robot_ban'),
    url(r"^about/$", nomination_about, name='nomination_about'),
    url(r"^help/$", nomination_help, name='nomination_help'),
    # url(r"^about/$", include('django.contrib.flatpages.urls'), name='nomination_about'),
    # url(r"^help/$", include('django.contrib.flatpages.urls'), name='nomination_help'),
    url(r"^([^/]+)/lookup/$", url_lookup, name='url_lookup'),
    url(r"^([^/]+)/search.json$", search_json, name='search_json'),
    url(r"^([^/]+)/browse/([^/]+)/browse.json$", browse_json, name='browse_json'),
    url(r"^([^/]+)/reports/projectdump/$", project_dump, name='project_dump'),
    url(r"^([^/]+)/reports/urls/score/$", url_score_report, name='url_score_report'),
    url(r"^([^/]+)/reports/urls/nomination/$", url_nomination_report,
        name='url_nomination_report'),
    url(r"^([^/]+)/reports/urls/date/$", url_date_report, name='url_date_report'),
    url(r"^([^/]+)/reports/urls/$", url_report, name='url_report'),
    url(r"^([^/]+)/reports/surts/$", surt_report, name='surt_report'),
    url(r"^([^/]+)/reports/metadata/(nominator|institution)/$", nominator_report,
        name='nominator_report'),
    url(r"^([^/]+)/reports/metadata/(nominator|institution)/([0-9]+)/$", nominator_url_report,
        name='nominator_url_report'),
    url(r"^([^/]+)/reports/metadata/([^/]+)/$", field_report, name='field_report'),
    # commented out line below for line under that in case user input value contains '/'
    # url(r"([^/]+)/reports/metadata/([^/]+)/([^/]+)/$", value_report, name='value_report'),
    url(r"^([^/]+)/reports/metadata/([^/]+)/((?:.|\s)+)/$", value_report, name='value_report'),
    url(r"^([^/]+)/reports/$", reports_view, name='reports_view'),
    url(r"^(?P<slug>[^/]+)/url/(?P<url_entity>[\w\W]+)/$", url_listing, name='url_listing'),
    url(r"^(?P<slug>[^/]+)/surt/(?P<surt>[\w\W]+)/$", url_surt, name='url_surt'),
    url(r"^([^/]+)/add/$", url_add, name='url_add'),
    url(r"^([^/]+)/about/$", project_about, name='project_about'),
    url(r"^([^/]+)/feed/nominations/$", nomination_feed(), name='nomination_feed'),
    url(r"^([^/]+)/feed/urls/$", url_feed(), name='url_feed'),
    url(r"^([^/]+)/$", project_urls, name='project_urls'),
]
