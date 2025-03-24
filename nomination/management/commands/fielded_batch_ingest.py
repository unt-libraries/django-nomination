import csv
import pickle
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from nomination.models import URL, Nominator, Project


# Global vars to speed up checking for existing records
surts_set = set()
nominator_urls_set = set()


class Command(BaseCommand):

    help = """fielded_batch_ingest - Adds urls from a text file into the URL table.

    Takes a list of urls from a text file (with a required project and nominator specified)
    and adds the urls to the URL table, adding a surt attribute if none exists.

    example: fielded_batch_ingest.py -p <PROJECT_SLUG> -n <NOMINATOR_ID> filename"""

    def add_arguments(self, parser):
        """Set command-line arguments."""
        parser.add_argument('file_name', help='input file')
        parser.add_argument('-n', '--nominator', dest='nominator_id', type=int, required=True,
                            help='identifies the nominator id number (required)')
        parser.add_argument('-p', '--project', dest='project_slug', required=True,
                            help='identifies the project slug (required)')
        file_type_group = parser.add_mutually_exclusive_group()
        file_type_group.add_argument('-c', '--csv', action='store_const', dest='ingest_function',
                                     const=csv_ingest, default=url_ingest,
                                     help='file is csv format')
        file_type_group.add_argument('-d', '--dict', action='store_const', dest='ingest_function',
                                     const=pydict_ingest, default=url_ingest,
                                     help='file is pickled dictionary format')
        parser.add_argument('--verify', action='store_true', dest='verify_url',
                            default=False, help='verify url is valid and available')

    def handle(self, *args, **options):
        """Ingest URLs from plain text, CSV, or pickled dictionary format file."""
        options['ingest_function'](options['file_name'], options['nominator_id'],
                                   options['project_slug'], options['verify_url'])


def url_ingest(file_name, nominator_id, project_slug, verify_url):
    """
        Get all the urls from the file and add them as a table entry to the
        URL table (not repeating if there is a prior entry with a surt).
    """

    # Make sure the project and nominator exist in the database
    project = get_project(project_slug)
    nominator = get_nominator(nominator_id)
    # Get the system nominator
    system_nominator = get_system_nominator()

    entry_count = 0
    new_entries = 0
    surt_entries = 0
    with open(file_name, 'r') as text_file:
        for line in text_file.readlines():
            if line.isspace():
                continue
            url_entity = url_formatter(line)
            if verify_url:
                if not verifyURL(url_entity):
                    continue
            # Attempt to create new url entry
            new_url = create_url_entry(project, nominator, url_entity, 'nomination', '1')
            # Create a SURT if the url doesn't already have one
            new_surt = create_url_entry(project, system_nominator, url_entity,
                                        'surt', surtize(url_entity))
            if new_url:
                new_entries += 1
            if new_surt:
                surt_entries += 1
            entry_count += 1
    print('Created %s new url surt entries.' % (surt_entries))
    print('Created %s new url nomination entries out of %s possible entries.'
          % (new_entries, entry_count))


def csv_ingest(file_name, nominator_id, project_slug, verify_url):
    # Make sure the project and nominator exist in the database
    project = get_project(project_slug)
    nominator = get_nominator(nominator_id)
    # Get the system nominator
    system_nominator = get_system_nominator()
    nominator_urls = list(URL.objects.filter(url_project=project,
                                             url_nominator=nominator).values('entity',
                                                                             'attribute',
                                                                             'value'))
    nominator_urls = ['{}{}{}'.format(i['entity'].lower(),
                                      i['attribute'].lower(),
                                      i['value'].lower()) for i in nominator_urls]
    global nominator_urls_set
    nominator_urls_set = set(nominator_urls)
    surts = list(URL.objects.filter(url_project=project,
                                    attribute='surt').values_list('entity', flat=True))
    surts = [s.lower() for s in surts]
    global surts_set
    surts_set = set(surts)
    nomination_count = 0
    entry_count = 0
    surt_count = 0
    new_entry = None
    with open(file_name, 'r', newline='') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for data in csv_reader:
            url_entity = url_formatter(data['url'])
            if verify_url:
                if not verifyURL(url_entity):
                    continue
            # Attempt to create new url nomination entry
            new_nomination = create_url_entry_less_db(project, nominator, url_entity, 'nomination',
                                                      '1')
            # Create a SURT if the url doesn't already have one
            new_surt = create_url_entry_less_db(project, system_nominator, url_entity, 'surt',
                                                surtize(url_entity))
            for attribute_name in data.keys():
                if not attribute_name == 'url':
                    if data[attribute_name] != '':
                        new_entry = create_url_entry_less_db(project, nominator, url_entity,
                                                             attribute_name, data[attribute_name])
                    if new_entry:
                        entry_count += 1

            if new_nomination:
                nomination_count += 1
            if new_surt:
                surt_count += 1
    print('Created %s new SURT entries.' % (surt_count))
    print('Created %s new nomination entries.' % (nomination_count))
    print('Created %s other attribute entries.' % (entry_count))


def pydict_ingest(file_name, nominator_id, project_slug, verify_url):
    """Ingest pickled dictionary into nomination tool.

    Useful for multivalue attributes that can be stored in the dictionary
    as lists.
    """
    # Make sure the project and nominator exist in the database
    project = get_project(project_slug)
    nominator = get_nominator(nominator_id)
    # Get the system nominator
    system_nominator = get_system_nominator()
    rff = open(file_name, 'r')
    nomination_count = 0
    entry_count = 0
    surt_count = 0
    new_entry = None
    # Process each subdomain
    while True:
        try:
            data = pickle.load(rff)
            url_entity = url_formatter(data['url'])
            if verify_url:
                if not verifyURL(url_entity):
                    continue
            # Attempt to create new url nomination entry
            new_nomination = create_url_entry(project, nominator, url_entity, 'nomination', '1')
            # Create a SURT if the url doesn't already have one
            new_surt = create_url_entry(project, system_nominator, url_entity, 'surt',
                                        surtize(url_entity))
            for attribute_name in data.keys():
                if not attribute_name == 'url' and data[attribute_name] != '':
                    # Check if the attribute has multiple values
                    if isinstance(data[attribute_name], list):
                        for val in data[attribute_name]:
                            new_entry = create_url_entry(project, nominator, url_entity,
                                                         attribute_name, val)
                            if new_entry:
                                entry_count += 1
                    else:
                        new_entry = create_url_entry(project, nominator, url_entity,
                                                     attribute_name, data[attribute_name])
                        if new_entry:
                            entry_count += 1

            if new_nomination:
                nomination_count += 1
            if new_surt:
                surt_count += 1
        except EOFError:
            break

    print('Created %s new SURT entries.' % (surt_count))
    print('Created %s new nomination entries.' % (nomination_count))
    print('Created %s other attribute entries.' % (entry_count))
    rff.close()


def get_nominator(nominator_id):
    try:
        nominator = Nominator.objects.get(id=nominator_id)
    except ObjectDoesNotExist:
        print('Nominator ID:%s was not found in the Nominator table. Please add the nominator,'
              ' or use the correct ID.' % (nominator_id))
        sys.exit()

    return nominator


def get_system_nominator():
    try:
        system_nominator = Nominator.objects.get(id=settings.SYSTEM_NOMINATOR_ID)
    except ObjectDoesNotExist:
        print('Could not get the system nominator.')
        sys.exit()

    return system_nominator


def get_project(slug):
    try:
        project = Project.objects.get(project_slug=slug)
    except ObjectDoesNotExist:
        print('%s was not found in the Project table. Please add the project to the'
              ' Project table.' % (slug))
        sys.exit()

    return project


def create_url_entry(project, nominator, url_entity, url_attribute, url_value):
    """Create a new url entry if it doesn't already exist."""
    try:
        if url_attribute == 'surt':
            URL.objects.get(url_project=project,
                            entity__iexact=url_entity,
                            attribute__iexact=url_attribute,
                            value__iexact=url_value
                            )
        else:
            URL.objects.get(url_project=project,
                            url_nominator=nominator,
                            entity__iexact=url_entity,
                            attribute__iexact=url_attribute,
                            value__iexact=url_value
                            )
    except ObjectDoesNotExist:
        try:
            URL.objects.create(url_project=project,
                               url_nominator=nominator,
                               entity=url_entity,
                               attribute=url_attribute,
                               value=url_value)
        except IntegrityError:
            print('Failed to create a new entry for url: %s attribute: %s value: %s'
                  % (url_entity, url_attribute, url_value))
            return False
    except MultipleObjectsReturned:
        print('Failed to create a new entry for url: %s attribute: %s value: %s'
              % (url_entity, url_attribute, url_value))
        return False
    else:
        return False
    return True


def create_url_entry_less_db(project, nominator, url_entity, url_attribute, url_value):
    """Create a new url entry if it doesn't already exist.

    This version of create_url_entry is much faster for large batches because
    of the reduction in database lookups, but to retain data integrity,
    do not process more than one file with this script per project at a time.
    """
    global surts_set
    global nominator_urls_set
    if url_attribute == 'surt':
        if url_entity.lower() in surts_set:
            return False
    else:
        key = '{}{}{}'.format(url_entity.lower(), url_attribute.lower(), url_value.lower())
        if key in nominator_urls_set:
            return False
    try:
        URL.objects.create(url_project=project,
                           url_nominator=nominator,
                           entity=url_entity,
                           attribute=url_attribute,
                           value=url_value)
        if url_attribute == 'surt':
            # Add entity for future lookups to surts_set.
            surts_set.add(url_entity.lower())
        else:
            # Add key for future value lookups.
            nominator_urls_set.add(key)
    except IntegrityError:
        print('Failed to create a new entry for url: %s attribute: %s value: %s'
              % (url_entity, url_attribute, url_value))
        return False
    return True


def url_formatter(line):
    """Format the given url into the proper url format."""
    url = line.strip().replace(' ', '%20')
    url = addImpliedHttpIfNecessary(url)
    url = url.rstrip('/')
    return url


def surtize(orig_url, preserveCase=False):
    """Create a surt from a url. Based on Heritrix's SURT.java."""
    # if url is submitted without scheme, add http://
    orig_url = addImpliedHttpIfNecessary(orig_url)

    # 1: scheme://
    # 2: userinfo (if present)
    # 3: @ (if present)
    # 4: dotted-quad host
    # 5: other host
    # 6: :port
    # 7: path
    # group def.      1          2                           3
    URI_SPLITTER = r"^(\w+://)(?:([-\w\.!~\*'\(\)%;:&=+$,]+?)(@))?" + \
                   r"(?:((?:\d{1,3}\.){3}\d{1,3})|(\S+?))(:\d+)?(/\S*)?$"
    #                   4                         5      6      7

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
    if mobj.group(4) is not None:
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

    # return surt
    if not preserveCase:
        return surt.lower()
    else:
        return surt


def appendToSurt(matchobj, groupnum, surt):
    if matchobj.group(groupnum) is not None:
        surt += matchobj.group(groupnum)
    return surt


def addImpliedHttpIfNecessary(uri):
    colon = uri.find(':')
    period = uri.find('.')
    if colon == -1 or (period >= 0 and period < colon):
        uri = 'http://' + uri
    return uri


class HeadRequest(Request):
    def get_method(self):
        return 'HEAD'


def verifyURL(url):
    """Test status response from URL."""
    try:
        url = url.encode('utf-8')
    except UnicodeEncodeError as e:
        print(str(e) + '; skipping URL ' + url)
        return False
    headers = {
        'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,'
                  'text/plain;q=0.8,image/png,*/*;q=0.5',
        'Accept-Language': 'en-us,en;q=0.5',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Connection': 'close',
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686)',
    }
    try:
        req = HeadRequest(url, None, headers)
        urlopen(req, timeout=5)
    except ValueError as e:
        print(str(e) + '; skipping invalid URL ' + url)
        return False
    except HTTPError as e:
        if e.code in (405, 501):
            # Try a GET request (HEAD refused)
            # See also: http://www.w3.org/Protocols/rfc2616/rfc2616.html
            try:
                req = Request(url, None, headers)
                urlopen(req, timeout=5)
            except (URLError, HTTPError):
                print(str(e) + '; Response: ' + str(e.code) + '; skipping URL ' + url)
                return False
        else:
            print(str(e) + '; Response: ' + str(e.code) + '; skipping URL ' + url)
            return False
    except (URLError, HTTPError):
        print('Failed HTTP response/broken link; skipping URL ' + url)
        return False
    return True
