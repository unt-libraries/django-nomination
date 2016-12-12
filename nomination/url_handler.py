import string, re, simplejson, itertools, datetime, time
from django import http
from django.conf import settings
from nomination.models import Project, Nominator, URL, Metadata, Value


SCHEME_ONE_SLASH = re.compile(r'(https?|ftps?):/([^/])')

def alphabetical_browse(project):
    browse_key_list = string.digits + string.uppercase
    browse_dict = {}
    try:
        surt_list = URL.objects.filter(url_project=project, attribute__iexact='surt').order_by('value')
    except:
        raise http.Http404

    #compile regex
    topdom_rgx = re.compile(r'^http://\(([^,]+),')
    singdom_rgx = re.compile(r'^http://\([^,]+,([^,\)]{1})')

    for url_item in surt_list:
        top_domain_search = topdom_rgx.search(url_item.value, 0)
        if top_domain_search:
            top_domain = top_domain_search.group(1)
            if not top_domain in browse_dict:
                browse_dict[top_domain] = {}
                for key in browse_key_list:
                    browse_dict[top_domain][key] = None
            domain_single_search = singdom_rgx.search(url_item.value, 0)
            if domain_single_search:
                domain_single = string.upper(domain_single_search.group(1))
                browse_dict[top_domain][domain_single] = domain_single_search.group(0)

    sorted_dict = {}
    for top_domain,alpha_dict in browse_dict.items():
        alpha_list = []
        for key in sorted(alpha_dict.iterkeys()):
            alpha_list.append((key, alpha_dict[key],))
        sorted_dict[top_domain] = alpha_list
    return sorted_dict

def get_metadata(project):
    """Creates metadata/values set to pass to template."""
    all_vals = None
    metadata_vals = []

    # combine values from value_sets and additional values
    for x in project.project_metadata_set.all():
        # get individual values in order by value_order
        all_vals = x.metadata.values.all().order_by('metadata_values')
        # get the set of value_sets and combine with other values
        for z in x.metadata.value_sets.all():
            all_vals = itertools.chain(z.values.all().order_by('valueset_values'), all_vals)
        metadata_vals.append((x, all_vals))

    return metadata_vals

def handle_metadata(request, posted_data):
    """Handles multivalue metadata and user supplied metadata values."""
    for k in posted_data.iterkeys():
        # if key has more than one value, post all
        requested_list = request.POST.getlist(k)
        if len(requested_list) > 1:
            # look for other_specify value
            for aval in requested_list:
                if aval == 'other_specify':
                    # add user input if there
                    try:
                        requested_list.append(posted_data[k+'_other'])
                    except:
                        pass
                    requested_list.remove(aval)
            posted_data[k] = requested_list
        else:
            # if other_specify value, supply user input
            if posted_data[k] == 'other_specify':
                try:
                    posted_data[k] = posted_data[k+'_other']
                except:
                    pass
    return posted_data

def validate_date(dateinput):
    """Takes user's date input and checks the validity.

    Returns a valid form of the date, or None if input was invalid.
    """
    DEFAULT_DATE_INPUT_FORMATS = (
        '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', # '2006-10-25', '10/25/2006', '10/25/06'
        '%b %d %Y', '%b %d, %Y',            # 'Oct 25 2006', 'Oct 25, 2006'
        '%d %b %Y', '%d %b, %Y',            # '25 Oct 2006', '25 Oct, 2006'
        '%B %d %Y', '%B %d, %Y',            # 'October 25 2006', 'October 25, 2006'
        '%d %B %Y', '%d %B, %Y',            # '25 October 2006', '25 October, 2006'
    )
    validdate = None
    if dateinput != None and \
      len(dateinput) != 0 and \
      not dateinput.isspace():
        for format in DEFAULT_DATE_INPUT_FORMATS:
            try:
                validdate = datetime.date(*time.strptime(dateinput, format)[:3])
                break
            except ValueError:
                continue
        return validdate

def add_url(project, form_data):
    summary_list = []
    form_data['url_value'] = check_url(form_data['url_value'])
    #Get the system nominator
    try:
        system_nominator = Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
    except:
        raise http.Http404

    #Check for or add surt
    surt_successful = surt_exists(project, system_nominator, form_data['url_value'])
    if not surt_successful:
        raise http.Http404

    #Get/Add a nominator
    nominator = get_nominator(form_data)
    if not nominator:
        raise http.Http404

    #Nominate a URL
    summary_list = nominate_url(project, nominator, form_data, '1')

    #Add other URL attributes
    summary_list = add_other_attribute(project, nominator, form_data, summary_list)

    return summary_list

def add_metadata(project, form_data):
    summary_list = []
    #Get/Add a nominator
    nominator = get_nominator(form_data)
    if not nominator:
        raise http.Http404

    if form_data['scope'] != '':
        #Nominate a URL
        summary_list = nominate_url(project, nominator, form_data, form_data['scope'])

    #Add other URL attributes
    summary_list = add_other_attribute(project, nominator, form_data, summary_list)

    return summary_list

def check_url(url):
    url = string.strip(url)
    if url.count('http://') > 1:
        url = url.replace('http://', '', 1)
    if url.startswith('https://'):
        url = url.replace('https://', 'http://', 1)
    url = addImpliedHttpIfNecessary(url)
    url = url.rstrip('/')
    return url

def get_nominator(form_data):
    try:
        #Try to retrieve the nominator
        nominator = Nominator.objects.get(nominator_email=form_data['nominator_email'])
    except:
        try:
            #Create a new nominator object
            nominator = Nominator(nominator_email=form_data['nominator_email'],
                                                  nominator_name=form_data['nominator_name'],
                                                  nominator_institution=form_data['nominator_institution'],
                                                 )
            nominator.save()
        except:
            return False

    return nominator

def nominate_url(project, nominator, form_data, scope_value):
    summary_list = []
    #Nominate URL
    try:
        #Check if user has already nominated the URL
        nomination_url = URL.objects.get(url_nominator__id__iexact = nominator.id,
                                                              url_project = project,
                                                              entity__iexact = form_data['url_value'],
                                                              attribute__iexact = 'nomination',
                                                             )
    except:
        try:
            #Nominate URL
            nomination_url = URL(entity = form_data['url_value'],
                                                value = scope_value,
                                                attribute = 'nomination',
                                                url_project = project,
                                                url_nominator = nominator,
                                               )
            nomination_url.save()
        except:
            raise http.Http404
        else:
            summary_list.append('You have successfully nominated ' + form_data['url_value'])
    else:
        if nomination_url.value == scope_value:
            if scope_value == '1':
                summary_list.append('You have already declared ' + form_data['url_value'] + ' as \"In Scope\"')
            else:
                summary_list.append('You have already declared ' + form_data['url_value'] + ' as \"Out of Scope\"')
        else:
            nomination_url.value = scope_value
            nomination_url.save()
            if scope_value == '1':
                summary_list.append('You have successfully declared ' + form_data['url_value'] + ' as \"In Scope\"')
            else:
                summary_list.append('You have successfully declared ' + form_data['url_value'] + ' as \"Out of Scope\"')

    return summary_list

def add_other_attribute(project, nominator, form_data, summary_list):
    # add to att_list the project specific attributes
    att_list = []

    for aobj in project.project_metadata_set.all():
        att_list.append(aobj.metadata.name)

    for attribute_name in att_list:
        #Add attribute URL entry
        if attribute_name in form_data:

            #If attribute has a list of values associated
            if isinstance(form_data[attribute_name], list):
                for oneval in form_data[attribute_name]:
                    if len(oneval) > 0:
                        summary_list = save_attribute(project, nominator, form_data, summary_list, attribute_name, oneval)

            elif len(form_data[attribute_name]) > 0:
                        summary_list = save_attribute(project, nominator, form_data, summary_list, attribute_name, form_data[attribute_name])

    return summary_list

def save_attribute(project, nominator, form_data, summary_list, attribute_name, valvar):
    """Stores attribute/value for given url in database.

    Separated out of add_other_attribute to handle attributes where a list
    of values was submitted.
    """
    try:
        #Check if URL attribute and value already exist
        added_url = URL.objects.get(url_nominator = nominator,
                                                 url_project = project,
                                                 entity__iexact = form_data['url_value'],
                                                 value__iexact = valvar,
                                                 attribute__iexact = attribute_name,
                                               )
    except:
        try:
            added_url = URL(entity = form_data['url_value'],
                                    value = valvar,
                                    attribute = attribute_name,
                                    url_project = project,
                                    url_nominator = nominator,
                                   )
            added_url.save()
        except:
            raise http.Http404
        else:
            summary_list.append('You have successfully added the ' + \
                attribute_name + ' \"' + valvar + '\" for ' + form_data['url_value'])
    else:
        summary_list.append('You have already added the ' + \
            attribute_name + ' \"' + valvar + '\" for ' + form_data['url_value'])

    return summary_list

def surt_exists(project, system_nominator, url_entity):
    #Create a SURT if the url doesn't already have one
    try:
        surt_url = URL.objects.get(url_project=project, entity__iexact=url_entity, attribute__iexact='surt')
    except:
        try:
            new_surt = URL(entity = url_entity,
                                      value = surtize(url_entity),
                                      attribute = 'surt',
                                      url_project = project,
                                      url_nominator = system_nominator,
                                     )
            new_surt.save()
        except:
            raise http.Http404

    return True

def url_formatter(line):
    """
        Formats the given url into the proper url format
    """
    url = string.strip(line)
    url = addImpliedHttpIfNecessary(url)

    return url

def surtize(orig_url, preserveCase=False):
    """
        Create a surt from a url. Based on Heritrix's SURT.java.
    """
    # if url is submitted without scheme, add http://
    orig_url = addImpliedHttpIfNecessary(orig_url)

    # 1: scheme://
    # 2: userinfo (if present)
    # 3: @ (if present)
    # 4: dotted-quad host
    # 5: other host
    # 6: :port
    # 7: path
    # group def.     1          2                           3
    URI_SPLITTER = "^(\w+://)(?:([-\w\.!~\*'\(\)%;:&=+$,]+?)(@))?" + \
        "(?:((?:\d{1,3}\.){3}\d{1,3})|(\S+?))(:\d+)?(/\S*)?$"
    #       4                         5      6      7

    # check URI validity
    m = re.compile(URI_SPLITTER)
    mobj = m.match(orig_url)
    if not mobj:
        return ''

    # start building surt form
    if mobj.group(1) == 'https://':
        surt = 'http://('
    else:
        surt = mobj.group(1) + '('
    # if dotted-quad ip match, don't reverse
    if mobj.group(4) != None:
        surt += mobj.group(4)
    # otherwise, reverse host
    else:
        splithost = mobj.group(5).split('.')
        splithost.reverse()
        hostpart = ','.join(splithost)
        surt += hostpart + ','
    # add port if it exists
    surt = appendToSurt(mobj, 6, surt)
    # add @ if it exists
    surt = appendToSurt(mobj, 3, surt)
    # add userinfo if it exists
    surt = appendToSurt(mobj, 2, surt)
    # close parentheses before path
    surt += ')'
    # add path if it exists
    surt = appendToSurt(mobj, 7, surt)

    #return surt
    if preserveCase == False:
        return surt.lower()
    else:
        return surt

def appendToSurt(matchobj, groupnum, surt):
    if matchobj.group(groupnum) != None:
        surt += matchobj.group(groupnum)
    return surt

def addImpliedHttpIfNecessary(uri):
    colon = uri.find(':')
    period = uri.find('.')
    if colon == -1 or (period >= 0 and period < colon):
       uri = 'http://' + uri
    return uri

def create_json_browse(slug, url_attribute, root):
    """Create a JSON list which can be used to represent a tree of the SURT domains.

    If a root is specified, the JSON list will show just the tree of domains under
    the specified base domain. Otherwise, it will show all of the domains. Each entry
    in the JSON list is a dict which states the base domain, child domain,
    and whether the child domain has children or not.
    """
    json_list = []

    #Make sure the project exist in the database
    try:
        project = Project.objects.get(project_slug=slug)
    except:
        raise http.Http404

    if root != '':
        #Find all URLs with the project and domain specified
        try:
            url_list = URL.objects.filter(url_project=project, attribute__iexact='surt', value__icontains=root).order_by('value')
        except:
            return ''
    else:
        #Find all URLs with the project specified (the base domains)
        try:
            url_list = URL.objects.filter(url_project=project, attribute__iexact='surt').order_by('value')
        except:
            return ''

    if len(url_list) >= 100 and root != '':
        category_list = []
        for url_item in url_list:
            name_search = re.compile(r'^http://\('+root+'([A-Za-z0-9]{1})').search(url_item.value, 0)
            if name_search:
                if not name_search.group(1) in category_list:
                    category_list.append(name_search.group(1))
        for category in category_list:
            category_dict = {'text': category,
                                       'id': root+category,
                                       'hasChildren': True
                                      }
            json_list.append(category_dict)
    else:
        for url_item in url_list:
            domain_dict = {}
            #Determine if URL is a child of the expanded node
            name_search = re.compile(r'^http://\('+root+'([^,\)]+)').search(url_item.value, 0)
            #if the URL exists under the expanded node
            if name_search:
                #Determine if the URL has children
                child_found = re.compile(r'^http://\('+root+'[^,]+,[^,\)]+').search(url_item.value, 0)
                #Create a new domain name for the new URL
                domain_name = root+name_search.group(1)
                domain_not_found = True
                #For all URLs in the json list already
                for existing_domain in json_list:
                    #Find the domain name within the anchor
                    found_anchor = re.compile(r'^<a href=\"[^>]+>([^<]+)</a>').search(existing_domain['text'], 0)
                    if found_anchor:
                        removed_anchor = found_anchor.group(1)
                    else:
                        removed_anchor = None
                    #if the domain name already exist in the json list
                    if existing_domain['text'] == domain_name or removed_anchor == domain_name:
                        domain_not_found = False
                        #if the domain name already exists in the json list, and it isn't listed as having children
                        if child_found and not 'hasChildren' in existing_domain:
                            existing_domain['hasChildren'] = True
                #if the domain hasn't been added already, and it has a child node
                if domain_not_found and child_found:
                    if len(domain_name.split(',')) > 1:
                        domain_dict = {'text': '<a href=\"surt/http://('+ \
                            domain_name+'\">'+ \
                            domain_name+'</a>',
                                       'id': domain_name+',',
                                       'hasChildren': True
                                      }
                    else:
                        domain_dict = {'text': domain_name,
                                       'id': domain_name+',',
                                       'hasChildren': True
                                      }
                #otherwise if the domain hasn't been added already, and it has no child
                elif domain_not_found:
                    domain_dict = {'text': '<a href=\"surt/http://('+ \
                        domain_name+'\">'+ \
                        domain_name+'</a>',
                                   'id': domain_name+','
                                  }
            #if the domain dictionary isn't empty
            if len(domain_dict) > 0:
                json_list.append(domain_dict)

    return simplejson.dumps(json_list)

def create_json_search(slug):
    """Create JSON list of all URLs added to the specified project."""
    try:
        project = Project.objects.get(project_slug=slug)
    except:
        raise http.Http404

    json_list = []
    query_list = (URL.objects.filter(url_project=project)
                             .values_list('entity', flat=True)
                             .distinct()
                             .order_by('entity'))
    for url_item in query_list:
        json_list.append(url_item)

    return simplejson.dumps(json_list)

def create_url_list(project, base_list):
    url_dict = {}
    for url_object in base_list:
        url_dict['entity'] = url_object.entity

        if url_object.attribute == 'nomination':
            if not 'nomination_list' in url_dict:
                url_dict['nomination_list'] = []
                url_dict['nomination_count'] = 0
                url_dict['nomination_score'] = 0
            if not url_object.url_nominator.nominator_name+ ' - ' + \
                url_object.url_nominator.nominator_institution \
                in url_dict['nomination_list']:
                url_dict['nomination_list'].append( \
                    url_object.url_nominator.nominator_name+ ' - ' + \
                    url_object.url_nominator.nominator_institution)
            url_dict['nomination_count'] += 1
            url_dict['nomination_score'] += int(url_object.value)
        elif url_object.attribute == 'surt':
            url_dict['surt'] = get_domain_surt(url_object.value)
        else:
            if not 'attribute_dict' in url_dict:
                url_dict['attribute_dict'] = {}
            attrib_key = string.capwords(url_object.attribute.replace('_', ' '))
            if not attrib_key in \
                   url_dict['attribute_dict']:
                url_dict['attribute_dict'][attrib_key] = []
            # try statement to replace value key with value value where applicable
            try:
                if len(project.project_metadata_set.get(metadata__name__exact=url_object.attribute).metadata.values.all()) > 0 or \
                   len(project.project_metadata_set.get(metadata__name__exact=url_object.attribute).metadata.value_sets.all()) > 0:
                    fullval = Value.objects.get(key__exact=url_object.value)
                    if not fullval in \
                        url_dict['attribute_dict'][attrib_key]:
                        url_dict['attribute_dict'][attrib_key].append( \
                            fullval)
                else:
                    raise Exception()
            except:
               if not url_object.value in \
                   url_dict['attribute_dict'][attrib_key]:
                   url_dict['attribute_dict'][attrib_key].append( \
                       url_object.value)
    return url_dict

def create_url_dump(project):
    url_dict = {}
    # get QuerySet of url_data
    entity_list = URL.objects.filter(url_project=project)
    # get metadata and values
    metadata_vals = get_metadata(project)
    # turn metadata_vals into usable dict
    val_dict = {}
    for met, vals in metadata_vals:
        val_dict[met.metadata.name] = {}
        for eachv in vals:
            val_dict[met.metadata.name][eachv.key] = eachv.value
    # merge the data for URLs with same entity
    for url_object in entity_list:
        url_ent = url_object.entity
        attrib_key = url_object.attribute
        # if first time we've seen the entity, create url_dict entry
        if url_ent not in url_dict.keys():
            url_dict[url_ent] = \
              {'nominators': [],
               'nomination_count': 0,
               'nomination_score': 0,
               'attributes': {},}
        if  attrib_key == 'nomination':
            nominator = url_object.url_nominator.nominator_name + ' - ' + \
              url_object.url_nominator.nominator_institution
            if not nominator in url_dict[url_ent]['nominators']:
                url_dict[url_ent]['nominators'].append(nominator)
            url_dict[url_ent]['nomination_count'] += 1
            url_dict[url_ent]['nomination_score'] += int(url_object.value)
        elif attrib_key == 'surt':
            url_dict[url_ent]['surt'] = url_object.value
            url_dict[url_ent]['domain_surt'] = get_domain_surt(url_object.value)
        else:
            if not attrib_key in url_dict[url_ent]['attributes'].keys():
                url_dict[url_ent]['attributes'][attrib_key] = []
            # replace value key with value value if applicable
            try:
                # see if the field has preset values
                if val_dict[attrib_key]:
                    fullval = unicode(val_dict[attrib_key][url_object.value])
                    if fullval not in \
                      url_dict[url_ent]['attributes'][attrib_key]:
                        url_dict[url_ent]['attributes'][attrib_key].append(fullval)
                else:
                    raise Exception()
            except:
                if not unicode(url_object.value) in \
                  url_dict[url_ent]['attributes'][attrib_key]:
                    url_dict[url_ent]['attributes'][attrib_key].append( \
                       unicode(url_object.value))
    # sort attribute lists
    for u, udata in url_dict.iteritems():
        if udata.get('attributes'):
            for att_key, att_vals in udata['attributes'].iteritems():
                att_vals.sort()
    return url_dict

def create_surt_dict(project, surt):
    try:
        url_list = URL.objects.filter(
            url_project=project,
            attribute__iexact='surt',
            value__istartswith=surt
        ).order_by('value')
    except:
        url_list = None

    letter = False
    single_letter_search = re.compile(r'^http://\([^,]+,([^,\)]+)').search(surt, 0)
    if single_letter_search:
        result = single_letter_search.group(1)
        if len(result) == 1:
            letter = result

    return {
        'url_list': url_list,
        'letter': letter,
    }

def get_domain_surt(surt):
    domain_surt = re.compile(r'^(http://\([^,]+,[^,]+,)').search(surt, 0)
    if domain_surt:
        return domain_surt.group(1)
    else:
        return surt

def fix_scheme_double_slash(url):
    """Add back slash lost by Apache removing null path segments."""
    fixed_entity = re.sub(SCHEME_ONE_SLASH, r'\1://\2', url)
    return fixed_entity
