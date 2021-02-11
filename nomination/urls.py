from django.urls import re_path, path
from nomination.views import (
    project_listing, robot_ban, nomination_about, nomination_help, url_lookup, search_json,
    browse_json, project_dump, url_score_report, url_nomination_report, url_date_report,
    url_report, surt_report, nominator_report, nominator_url_report, field_report, value_report,
    reports_view, url_listing, url_surt, url_add, project_about, project_urls
)
from nomination.feeds import url_feed, nomination_feed

urlpatterns = [
    path("", project_listing, name='project_listing'),
    path("robots.txt", robot_ban, name='robot_ban'),
    path("about/", nomination_about, name='nomination_about'),
    path("help/", nomination_help, name='nomination_help'),
    path("<slug>/lookup/", url_lookup, name='url_lookup'),
    path("<slug>/search.json", search_json, name='search_json'),
    path("<slug>/browse/<attribute>/browse.json", browse_json, name='browse_json'),
    path("<slug>/reports/projectdump/", project_dump, name='project_dump'),
    path("<slug>/reports/urls/score/", url_score_report, name='url_score_report'),
    path("<slug>/reports/urls/nomination/", url_nomination_report,
         name='url_nomination_report'),
    path("<slug>/reports/urls/date/", url_date_report, name='url_date_report'),
    path("<slug>/reports/urls/", url_report, name='url_report'),
    path("<slug>/reports/surts/", surt_report, name='surt_report'),
    re_path(r"^([^/]+)/reports/metadata/(nominator|institution)/$", nominator_report,
            name='nominator_report'),
    re_path(r"^([^/]+)/reports/metadata/(nominator|institution)/([0-9]+)/$", nominator_url_report,
            name='nominator_url_report'),
    path("<slug>/reports/metadata/<field>/", field_report, name='field_report'),
    re_path(r"^([^/]+)/reports/metadata/([^/]+)/((?:.|\s)+)/$", value_report, name='value_report'),
    path("<slug>/reports/", reports_view, name='reports_view'),
    path("<slug>/url/<path:url_entity>/", url_listing, name='url_listing'),
    path("<slug>/surt/<path:surt>/", url_surt, name='url_surt'),
    path("<slug>/add/", url_add, name='url_add'),
    path("<slug>/about/", project_about, name='project_about'),
    path("<slug>/feed/nominations/", nomination_feed(), name='nomination_feed'),
    path("<slug>/feed/urls/", url_feed(), name='url_feed'),
    path("<slug>/", project_urls, name='project_urls'),
]
