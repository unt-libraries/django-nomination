import json
import datetime
import re
import urllib

from django.shortcuts import render, get_object_or_404
from django import http
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.db.models import Sum, Count, Max
from django import forms
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django.contrib.sites.models import Site

from nomination.models import Project, URL, Nominator
from nomination.url_handler import (
    add_url, create_json_browse, create_url_list, create_json_search,
    add_metadata, fix_scheme_double_slash, create_surt_dict,
    alphabetical_browse, get_metadata, handle_metadata, validate_date,
    create_url_dump, strip_scheme
)


SCOPE_CHOICES = (('1', 'In Scope',),
                 ('-1', 'Out of Scope',),)


class URLForm(forms.Form):
    url_value = forms.URLField(
        required=True,
        widget=forms.TextInput(attrs={'name': 'url-value', 'id': 'url-value'})
    )
    nominator_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'name': 'your-name-value', 'id': 'your-name-value'})
    )
    nominator_email = forms.EmailField(
        required=False,
        widget=forms.TextInput(attrs={'name': 'email-value', 'id': 'email-value'})
    )
    nominator_institution = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'name': 'institution-value', 'id': 'institution-value', 'autocomplete': 'off'}
        )
    )


class ScopeForm(forms.Form):
    scope = forms.ChoiceField(
        required=False,
        choices=SCOPE_CHOICES,
        widget=forms.RadioSelect(attrs={'name': 'scope-value'}))
    nominator_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'name': 'your-name-value', 'id': 'your-name-value'})
    )
    nominator_email = forms.EmailField(
        required=False,
        widget=forms.TextInput(attrs={'name': 'email-value', 'id': 'email-value'}))
    nominator_institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'name': 'institution-value', 'id': 'institution-value'})
    )


def project_listing(request):
    # get the project by the project slug
    try:
        projects_list = Project.objects.all().order_by('project_name')
        active_list = projects_list.filter(
          project_start__lte=datetime.datetime.now(),
          project_end__gte=datetime.datetime.now())
        past_list = projects_list.exclude(
          project_start__lte=datetime.datetime.now(),
          project_end__gte=datetime.datetime.now())
    except Exception:
        raise http.Http404

    return render(
        request,
        'nomination/project_listing.html',
        {
            'active_list': active_list,
            'past_list': past_list,
        },
    )


def robot_ban(request):
    return HttpResponse('User-agent: *' + "\n" + 'Disallow: /', content_type='text/plain')


def nomination_about(request):
    return render(
        request,
        'nomination/about.html',
    )


def nomination_help(request):
    return render(
        request,
        'nomination/help.html',
    )


def url_lookup(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    # handle the post
    if request.method == 'POST':
        posted_data = dict(request.POST.copy())
        if 'search-url-value' in posted_data:
            url_entity = posted_data['search-url-value'][0].strip().rstrip('/')
            if 'partial-search' in posted_data or not url_entity:
                url_list = URL.objects.filter(
                    url_project=project,
                    attribute__iexact='surt',
                    entity__icontains=strip_scheme(url_entity)
                ).order_by('value')
                if url_list:
                    return render(
                        request,
                        'nomination/url_search_results.html',
                        {'project': project, 'url_list': url_list}
                    )
            if 'partial-search' not in posted_data and url_entity:
                # check for scheme agnostic url matches
                url_list = URL.objects.filter(
                    url_project=project,
                    attribute__iexact='surt',
                    entity__endswith='://'+strip_scheme(url_entity)
                ).values_list('entity', flat=True)
                if url_list:
                    # allow URL with a different scheme if available
                    if url_entity not in url_list:
                        url_entity = url_list[0]
            # redirect if partial-search was empty or for non partial-search
            redirect_url = iri_to_uri('/nomination/%s/url/%s/' % (slug, urlquote(url_entity)))
        else:
            raise http.Http404
    else:
        raise http.Http404

    return HttpResponseRedirect(redirect_url)


@csrf_protect
def project_urls(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    # Create the alphabetical browse dictionary
    browse_tup = sorted(tuple(alphabetical_browse(project).items()))

    # get general project statistics
    urls = URL.objects.filter(url_project__project_slug__exact=slug)
    url_count = get_project_url_count(urls)
    nominator_count = get_project_nominator_count(urls)

    return render(
        request,
        'nomination/project_urls.html',
        {
         'project': project,
         'browse_tup': browse_tup,
         'url_count': url_count,
         'nominator_count': nominator_count,
        },
        )


@csrf_protect
def url_listing(request, slug, url_entity):
    # Add back the slash lost by Apache removing null path segments.
    url_entity = fix_scheme_double_slash(url_entity)
    url_exists = True
    posted_data = None
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    # get list of institutions to populate autocomplete
    institutions = get_look_ahead(project)

    # create metadata/values set
    metadata_vals = get_metadata(project)
    # get the list of URLs
    try:
        find_url = URL.objects.filter(entity__iexact=url_entity, url_project=project)
    except Exception:
        url_exists = False

    if url_exists and len(find_url) > 0:
        form_errors = None
        summary_list = None
        if request.method == 'POST':
            posted_data = request.POST.copy()
            scope_form = ScopeForm(posted_data)
            form_errors = scope_form.errors
            some_errors = {}
            # check validity of dates
            for met in project.project_metadata_set.all().filter(form_type='date'):
                if met.metadata.name in posted_data:
                    if not posted_data[met.metadata.name]:
                        # added this 'if' when iipc wanted not to require any fields
                        # on url_listing edit form
                        continue
                    cleandate = validate_date(posted_data[met.metadata.name])
                    if cleandate:
                        cleandate = str(cleandate)
                        # check if this fits valid date range.

                        # The following code presumes (too much) if there are
                        # values associated with this metadata date field, the
                        # first date will be the default value for the form. If
                        # two dates are given, in addition to the first date
                        # being the form default, it will be the start of a
                        # range, while the second value will be the end of that
                        # range. If three values are given, the first value is,
                        # as always, default for the form, and the next 2 dates
                        # serve as the start and end points of the valid range.
                        datevals = met.metadata.values.all().order_by('metadata_values')
                        numvals = len(datevals)
                        if numvals > 1:
                            if numvals == 2:
                                rangestart = datevals[0].value
                                rangeend = datevals[1].value
                            elif numvals > 2:
                                rangestart = datevals[1].value
                                rangeend = datevals[2].value
                            if not (cleandate >= rangestart and
                                    cleandate <= rangeend):
                                some_errors[met.metadata.name] = \
                                    'The date you entered is outside the allowed range.'
                            else:
                                # store the valid date
                                posted_data[met.metadata.name] = cleandate
                        else:
                            posted_data[met.metadata.name] = cleandate
                    else:
                        some_errors[met.metadata.name] = \
                            'Enter a valid date format.'
            # check validity of standard metadata
            if scope_form.is_valid():
                # check if nominator is required by project
                nominator_fields = ['nominator_name',
                                    'nominator_email',
                                    'nominator_institution']
                if project.registration_required:
                    for nominator_field in nominator_fields:
                        if not scope_form.cleaned_data[nominator_field].strip():
                            some_errors[nominator_field] = \
                                'This field is required.'
                else:
                    if scope_form.cleaned_data['nominator_name'].strip() or\
                            scope_form.cleaned_data['nominator_institution'].strip() or\
                            scope_form.cleaned_data['nominator_email'].strip():
                        for nominator_field in nominator_fields:
                            if not scope_form.cleaned_data[nominator_field].strip():
                                some_errors[nominator_field] = \
                                    ('You must provide name, institution, and email '
                                     'to affiliate your name or institution '
                                     'with nominations. Leave all "Information '
                                     'About You" fields blank to remain anonymous.')
                    else:
                        # supply anonymous information
                        scope_form.cleaned_data['nominator_email'] = 'anonymous'
                        scope_form.cleaned_data['nominator_name'] = 'Anonymous'
                        scope_form.cleaned_data['nominator_institution'] = 'Anonymous'
                if not some_errors:
                    # combine cleaned form class data with project specific data
                    posted_data.update(scope_form.cleaned_data)
                    # handle multivalue metadata and user supplied values
                    posted_data = handle_metadata(request, posted_data)

                    posted_data['url_value'] = url_entity
                    summary_list = add_metadata(project, posted_data)

                    # clear out posted data, so it is not sent back to form
                    posted_data = None
                else:
                    form_errors.update(some_errors)
        else:
            # Create the scope form
            scope_form = ScopeForm()

        # Create a dictionary from the URLs information pulled from all the URLs entries
        url_list = URL.objects.filter(
            entity__iexact=url_entity,
            url_project=project
        ).order_by('attribute')
        url_data = create_url_list(project, url_list)
        # Grab all related URLs
        try:
            related_url_list = URL.objects.filter(
                url_project=project,
                attribute__iexact='surt',
                value__istartswith=url_data['surt']
            ).order_by('value').exclude(entity__iexact=url_entity)
        except Exception:
            related_url_list = None

        # in case of a user input error, send back data to repopulate form
        json_data = None
        if posted_data:
            json_data = json.dumps(list(posted_data.lists()))

        # send form types for use to repopulate form
        form_types = {}
        for pm in project.project_metadata_set.all():
            form_types[pm.metadata.name] = str(pm.form_type)

        return render(
            request,
            'nomination/url_listing.html',
            {
             'project': project,
             'url_data': url_data,
             'related_url_list': related_url_list,
             'scope_form': scope_form,
             'form_errors': form_errors,
             'summary_list': summary_list,
             'metadata_vals': metadata_vals,
             'json_data': json_data,
             'form_types': json.dumps(form_types),
             'institutions': institutions,
            },
            )
    else:
        default_data = {'url_value': url_entity}
        form = URLForm(default_data)
        return render(
            request,
            'nomination/url_add.html',
            {
             'project': project,
             'form': form,
             'url_not_found': True,
             'metadata_vals': metadata_vals,
             'form_errors': None,
             'summary_list': None,
             'json_data': None,
             'form_types': None,
             'institutions': institutions,
             'url_entity': url_entity,
            },
            )


def url_surt(request, slug, surt):
    # Add back the slash lost by Apache removing null path segments.
    surt = fix_scheme_double_slash(surt)
    # Get the project by the project slug.
    project = get_object_or_404(Project, project_slug=slug)
    # Create the SURT dictionary containing url_list and single_letter.
    surt_dict = create_surt_dict(project, surt)
    # Create the alphabetical browse dictionary.
    browse_dict = alphabetical_browse(project)
    # Add Browse by if browsing surts by letter.
    top_domain_search = re.compile(r'^(?:[^:]+://)?\(([^,]+),?').search(surt, 0)
    if top_domain_search:
        top_domain = top_domain_search.group(1)
    else:
        top_domain = None
    return render(
        request,
        'nomination/url_surt.html',
        {
            'surt': surt,
            'project': project,
            'url_list': surt_dict['url_list'],
            'letter': surt_dict['letter'],
            'browse_domain': top_domain,
            'browse_dict': browse_dict,
        },
    )


@csrf_protect
def url_add(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)
    # handle the post
    form_errors = None
    # get list of institutions to populate autocomplete
    institutions = get_look_ahead(project)
    some_errors = {}
    summary_list = []
    req_fields = project.project_metadata_set.filter(required=True)
    date_fields = project.project_metadata_set.filter(form_type='date')
    posted_data = None
    url_entity = None

    if request.method == 'POST':
        posted_data = request.POST.copy()

        form = URLForm(posted_data)
        form_errors = form.errors
        # check for required fields of project specific metadata
        for met in req_fields:
            if met.metadata.name not in posted_data or len(posted_data[met.metadata.name]) == 0 \
                    or posted_data[met.metadata.name].isspace():
                some_errors[met.metadata.name] = 'This field is required.'
        # check validity of dates
        for met in date_fields:
            if met not in req_fields and not posted_data[met.metadata.name]:
                pass
            elif met.metadata.name in posted_data:
                cleandate = validate_date(posted_data[met.metadata.name])
                if cleandate:
                    cleandate = str(cleandate)
                    # check if this fits valid date range.

                    # The following code presumes (too much) if there are
                    # values associated with this metadata date field, the
                    # first date will be the default value for the form. If
                    # two dates are given, in addition to the first date
                    # being the form default, it will be the start of a
                    # range, while the second value will be the end of that
                    # range. If three values are given, the first value is,
                    # as always, default for the form, and the next 2 dates
                    # serve as the start and end points of the valid range.
                    datevals = met.metadata.values.all().order_by('metadata_values')
                    numvals = len(datevals)
                    if numvals > 1:
                        if numvals == 2:
                            rangestart = datevals[0].value
                            rangeend = datevals[1].value
                        elif numvals > 2:
                            rangestart = datevals[1].value
                            rangeend = datevals[2].value
                        if not (cleandate >= rangestart and
                                cleandate <= rangeend):
                            some_errors[met.metadata.name] = \
                                'The date you entered is outside the allowed range.'
                        else:
                            # store the valid date
                            posted_data[met.metadata.name] = cleandate
                    else:
                        posted_data[met.metadata.name] = cleandate
                else:
                    some_errors[met.metadata.name] = 'Please enter a valid date format.'

        # check validity of standard metadata
        # check if nominator is required by project
        nominator_fields = ['nominator_name',
                            'nominator_email',
                            'nominator_institution']
        if project.registration_required:
            for nominator_field in nominator_fields:
                if not posted_data[nominator_field].strip():
                    some_errors[nominator_field] = \
                        'This field is required.'
        else:
            if posted_data['nominator_name'].strip() or\
                    posted_data['nominator_institution'].strip() or\
                    posted_data['nominator_email'].strip():
                for nominator_field in nominator_fields:
                    if not posted_data[nominator_field].strip():
                        some_errors[nominator_field] = \
                            ('You must provide name, institution, and email to '
                             'affiliate your name or institution with '
                             'nominations. Leave all "Information '
                             'About You" fields blank to remain anonymous.')
        if form.is_valid():
            if not form.cleaned_data['url_value'].strip() == 'http://':
                # summary_list = add_url(project, form.cleaned_data)
                if not some_errors:
                    # combine form class data with project specific data
                    posted_data.update(form.cleaned_data)
                    if not posted_data['nominator_email'].strip():
                        # set anonymous user
                        posted_data['nominator_email'] = 'anonymous'
                        posted_data['nominator_name'] = 'Anonymous'
                        posted_data['nominator_institution'] = 'Anonymous'
                    # handle multivalue metadata and user supplied values
                    posted_data = handle_metadata(request, posted_data)

                    summary_list = add_url(project, posted_data)
                    # send url value to provide metadata link
                    url_entity = posted_data['url_value']
                    # clear out posted data, so it is not sent back to form
                    posted_data = None

                else:
                    form_errors.update(some_errors)
            else:
                form_errors = 'Please specify the URL'
        else:
            form_errors.update(some_errors)

    form = URLForm()

    # create metadata/values set
    metadata_vals = get_metadata(project)

    if not len(summary_list) > 0:
        summary_list = None

    # in case of an error, send back data to repopulate form
    json_data = None
    if posted_data:
        json_data = json.dumps(list(posted_data.lists()))

    # send form types for use to repopulate form
    form_types = {}
    for pm in project.project_metadata_set.all():
        form_types[pm.metadata.name] = str(pm.form_type)

    return render(
        request,
        'nomination/url_add.html',
        {
         'project': project,
         'form': form,
         'form_errors': form_errors,
         'summary_list': summary_list,
         'metadata_vals': metadata_vals,
         'json_data': json_data,
         'form_types': json.dumps(form_types),
         'institutions': institutions,
         'url_entity': url_entity,
        },
        )


def project_about(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)
    # get general project statistics
    urls = URL.objects.filter(url_project__project_slug__exact=slug)
    url_count = get_project_url_count(urls)
    nominator_count = get_project_nominator_count(urls)
    current_host = get_object_or_404(Site, id=settings.SITE_ID)
    # figure out if we need to show bookmarklets
    show_bookmarklets = datetime.datetime.now() < project.nomination_end
    return render(
        request,
        'nomination/project_about.html',
        {
         'project': project,
         'url_count': url_count,
         'nominator_count': nominator_count,
         'current_host': current_host,
         'show_bookmarklets': show_bookmarklets,
        },
        )


def get_project_url_count(urls):
    # get count of urls nominated to this project
    return urls.filter(attribute__exact="surt").count()


def get_project_nominator_count(urls):
    # get count of unique nominators to project
    return urls.filter(attribute__exact='nomination').filter(
      value__exact=1).values_list(
      'url_nominator', flat=True).distinct().count()


def browse_json(request, slug, attribute):
    """Return a page with a JSON list representing a domain tree for added URLs."""
    if request.method == 'GET':
        # Root is the id of the expand link clicked
        if 'root' in request.GET:
            root = request.GET['root']
            # No id specified
            if root == 'source':
                root = ''
            json_string = create_json_browse(slug, attribute, root)
        else:
            json_string = create_json_browse(slug, attribute, '')
    else:
        json_string = create_json_browse(slug, attribute, '')

    return HttpResponse(json_string, content_type='application/json')


def search_json(request, slug):
    """Return a page with a JSON list of all URLs added to the specified project."""
    json_string = create_json_search(slug)

    return HttpResponse(json_string, content_type='application/json')


def reports_view(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    # get list of attributes from url table for metadata report
    results = (URL.objects.filter(url_project__id=project.id)
                  .exclude(attribute='nomination')
                  .exclude(attribute='surt')
                  .distinct()
                  .values_list('attribute'))

    return render(
        request,
        'nomination/reports.html',
        {
         'project': project,
         'metadata_fields': results,
        },
        )


def url_report(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    # get the list of URLs
    try:
        url_list = URL.objects.filter(
            attribute__iexact='surt',
            url_project=project
        ).order_by('value')
    except Exception:
        raise http.Http404

    # Create the first two lines of the report file
    report_text = '#This list of urls was created for the ' + project.project_name + \
                  ' project.\n#Unique URLs sorted by SURT\n#List generated on ' + \
                  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%SZ') + '\n\n'

    for url_item in url_list:
        report_text += url_item.entity + "\n"

    return HttpResponse(report_text, content_type='text/plain; charset="UTF-8"')


def surt_report(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    # get the list of URLs
    try:
        surt_list = URL.objects.filter(
            attribute__iexact='surt',
            url_project=project
        ).values_list('value', flat=True).distinct().order_by('value')
    except Exception:
        raise http.Http404

    # Create the first two lines of the report file
    report_text = '#This list of SURTs was created for the ' + project.project_name + \
                  ' project.\n#SURTs sorted by SURT\n#List generated on ' + \
                  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%SZ') + '\n\n'

    for url_item in surt_list:
        report_text += url_item + "\n"

    return HttpResponse(report_text, content_type='text/plain; charset="UTF-8"')


def url_score_report(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    results = (URL.objects.values('entity')
                  .annotate(nomination_score=Sum('value'))
                  .filter(url_project__id=project.id, attribute='nomination')
                  .order_by('-nomination_score')
                  .values_list('nomination_score', 'entity'))

    report_text = '#This list of URLs was created for the ' + project.project_name + \
                  ' project.\n#URLs and overall nomination score\n' + \
                  '#List generated on ' + \
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%SZ") + "\n\n"

    for row in results:
        nomination_score, entity = row
        report_text += '{0};"{1}"\n'.format(int(nomination_score), entity)

    return HttpResponse(report_text, content_type='text/plain; charset="UTF-8"')


def url_date_report(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    results = (URL.objects.extra(select={'nomination_date': 'date'})
                  .filter(url_project__id=project.id, attribute='nomination')
                  .order_by('nomination_date')
                  .values_list('nomination_date', 'entity', 'value'))

    report_text = '#This list of URLs was created for the ' + project.project_name + \
                  ' project.\n#Nomination date, URL, and in/out of scope are given\n' +\
                  '#List generated on ' + \
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%SZ") + "\n\n"

    for row in results:
        date, entity, value = row
        report_text += '{0};"{1}";{2}\n'.format(date.strftime('%Y-%m-%dT%H:%M:%S'),
                                                entity, value)

    return HttpResponse(report_text, content_type='text/plain; charset="UTF-8"')


def url_nomination_report(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)

    results = (URL.objects.values('entity')
                  .annotate(nominations=Count('entity'))
                  .filter(url_project__id=project.id, attribute='nomination')
                  .order_by('-nominations')
                  .values_list('nominations', 'entity'))

    report_text = '#This list of URLs was created for the ' + project.project_name + \
                  ' project.\n#URLs and number of nominations ' + \
                  '(could be either positive or negative nominations)\n' + \
                  '#List generated on ' + \
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%SZ") + "\n\n"

    for row in results:
        nominations, entity = row
        report_text += '{0};"{1}"\n'.format(int(nominations), entity)

    return HttpResponse(report_text, content_type='text/plain; charset="UTF-8"')


def field_report(request, slug, field):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)
    namelist = []

    results = (URL.objects.filter(url_project__id=project.id, attribute=field)
                  .values('value')
                  .order_by('value')
                  .annotate(count=Count('entity', distinct=True))
                  .values_list('value', 'count'))

    try:
        # create values set -- if metadata is in metadata field table
        mobj = project.project_metadata_set.get(metadata__name__iexact=field).metadata
        all_vals = mobj.values.all()
        # combine values from value_sets and additional values
        val_sets = mobj.value_sets.all()
        for z in val_sets:
            all_vals = z.values.all() | all_vals
        valset = all_vals.values('key', 'value')
        if len(valset) > 0:
            kvdict = {}
            for it in valset:
                kvdict[it['key']] = it['value']
            for row in results:
                value, count = row
                if value in kvdict.keys():
                    namelist.append((kvdict[value], count, value))
                else:
                    namelist.append((value, count, value))
    except Exception:
        pass

    return render(
        request,
        'nomination/metadata_report.html',
        {
         'project': project,
         'valdic': results,
         'namelist': namelist,
         'field': field,
        },
        )


def value_report(request, slug, field, val):
    val = urllib.parse.unquote(val)
    # Add back the slash lost by Apache removing null path segments.
    val = fix_scheme_double_slash(val)
    # Get the project by the project slug.
    project = get_object_or_404(Project, project_slug=slug)
    # If there are no URLs in the queryset, Apache rewrote the url,
    # so we need to add a trailing slash to do a lookup properly.
    urls = URL.objects.filter(url_project_id=project.id, attribute=field, value=val)
    if urls.count() == 0:
        val = val + '/'
        urls = URL.objects.filter(url_project_id=project.id, attribute=field, value=val)
    report_text = '#This list of URLs was created for the ' + project.project_name + \
                  ' project.\n#URLs for value "' + val + '" in metadata field "' + \
                  field + '"\n' + \
                  '#List generated on ' + \
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%SZ") + "\n\n"
    for entity in urls.values_list('entity', flat=True).order_by('entity').distinct():
        report_text += entity + '\n'
    return HttpResponse(report_text, content_type='text/plain;')


def nominator_report(request, slug, field):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)
    if field == 'nominator':
        fieldname = 'nominator_name'
        groupby = 'id'
    else:
        fieldname = groupby = 'nominator_institution'

    results = (URL.objects.filter(url_project=project.id,
                                  attribute='nomination',
                                  value=1)
                  .values('url_nominator__{}'.format(groupby))
                  .order_by('url_nominator__{}'.format(fieldname))
                  .annotate(count=Count('entity'), nomid=Max('url_nominator__id'))
                  .values_list('url_nominator__{}'.format(fieldname), 'count', 'nomid'))

    return render(
        request,
        'nomination/nominator_report.html',
        {
         'project': project,
         'valdic': results,
         'field': field,
        },
        )


def nominator_url_report(request, slug, field, nomid):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)
    if field == 'nominator':
        # get nominator name
        nomname = get_object_or_404(Nominator, id=nomid).nominator_name

        results = (URL.objects.filter(url_project=project.id,
                                      url_nominator=nomid,
                                      attribute='nomination',
                                      value=1)
                      .order_by('entity')
                      .values_list('entity', flat=True)
                      .distinct())
    else:
        # get institution name
        nomname = get_object_or_404(Nominator, id=nomid).nominator_institution

        results = (URL.objects.filter(url_project=project.id,
                                      url_nominator__nominator_institution=nomname,
                                      attribute='nomination',
                                      value=1)
                      .order_by('entity')
                      .values_list('entity', flat=True)
                      .distinct())

    report_text = ('#This list of URLs was created for the ' + project.project_name +
                   ' project.\n#URLs for ' + field + ' "' + nomname + '"\n' +
                   '#List generated on ' +
                   datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%SZ") + '\n\n')
    for entity in results:
        report_text += entity + '\n'

    return HttpResponse(report_text, content_type='text/plain; charset="UTF-8"')


def project_dump(request, slug):
    # get the project by the project slug
    project = get_object_or_404(Project, project_slug=slug)
    project_urls = {}
    # Create dictionary from the URLs data pulled from all URLs entries
    project_urls = create_url_dump(project)
    response = HttpResponse(content_type='application/json; charset=utf-8')
    json.dump(project_urls, fp=response, sort_keys=True, indent=4, ensure_ascii=False)
    response['Content-Disposition'] = 'attachment; filename=' + slug + '_urls.json'
    return response


def get_look_ahead(project):
    """Returns nominating institution list."""
    nominator_list = URL.objects.filter(
      url_project__exact=project.id).select_related(
      'url_nominator__nominator_institution').values_list(
      'url_nominator__nominator_institution', flat=True).distinct().order_by(
      'url_nominator__nominator_institution')

    return json.dumps(list(nominator_list))
