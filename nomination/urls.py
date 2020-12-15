from django.urls import re_path
from nomination.views import (
    project_listing, robot_ban, nomination_about, nomination_help, url_lookup, search_json,
    browse_json, project_dump, url_score_report, url_nomination_report, url_date_report,
    url_report, surt_report, nominator_report, nominator_url_report, field_report, value_report,
    reports_view, url_listing, url_surt, url_add, project_about, project_urls
)
from nomination.feeds import url_feed, nomination_feed

urlpatterns = [
    re_path(r"^$", project_listing, name='project_listing'),
    re_path(r"^robots.txt$", robot_ban, name='robot_ban'),
    re_path(r"^about/$", nomination_about, name='nomination_about'),
    re_path(r"^help/$", nomination_help, name='nomination_help'),
    re_path(r"^([^/]+)/lookup/$", url_lookup, name='url_lookup'),
    re_path(r"^([^/]+)/search.json$", search_json, name='search_json'),
    re_path(r"^([^/]+)/browse/([^/]+)/browse.json$", browse_json, name='browse_json'),
    re_path(r"^([^/]+)/reports/projectdump/$", project_dump, name='project_dump'),
    re_path(r"^([^/]+)/reports/urls/score/$", url_score_report, name='url_score_report'),
    re_path(r"^([^/]+)/reports/urls/nomination/$", url_nomination_report,
            name='url_nomination_report'),
    re_path(r"^([^/]+)/reports/urls/date/$", url_date_report, name='url_date_report'),
    re_path(r"^([^/]+)/reports/urls/$", url_report, name='url_report'),
    re_path(r"^([^/]+)/reports/surts/$", surt_report, name='surt_report'),
    re_path(r"^([^/]+)/reports/metadata/(nominator|institution)/$", nominator_report,
            name='nominator_report'),
    re_path(r"^([^/]+)/reports/metadata/(nominator|institution)/([0-9]+)/$", nominator_url_report,
            name='nominator_url_report'),
    re_path(r"^([^/]+)/reports/metadata/([^/]+)/$", field_report, name='field_report'),
    # commented out line below for line under that in case user input value contains '/'
    # re_path(r"([^/]+)/reports/metadata/([^/]+)/([^/]+)/$", value_report, name='value_report'),
    re_path(r"^([^/]+)/reports/metadata/([^/]+)/((?:.|\s)+)/$", value_report, name='value_report'),
    re_path(r"^([^/]+)/reports/$", reports_view, name='reports_view'),
    re_path(r"^(?P<slug>[^/]+)/url/(?P<url_entity>[\w\W]+)/$", url_listing, name='url_listing'),
    re_path(r"^(?P<slug>[^/]+)/surt/(?P<surt>[\w\W]+)/$", url_surt, name='url_surt'),
    re_path(r"^([^/]+)/add/$", url_add, name='url_add'),
    re_path(r"^([^/]+)/about/$", project_about, name='project_about'),
    re_path(r"^([^/]+)/feed/nominations/$", nomination_feed(), name='nomination_feed'),
    re_path(r"^([^/]+)/feed/urls/$", url_feed(), name='url_feed'),
    re_path(r"^([^/]+)/$", project_urls, name='project_urls'),
]
