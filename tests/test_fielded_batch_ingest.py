import datetime
import pathlib
from unittest.mock import patch, Mock

from django.core.management import call_command
from django.db import IntegrityError
import pytest

from nomination.management.commands import fielded_batch_ingest
from nomination.models import URL
from . import factories


TEST_DIR = pathlib.Path(__file__).resolve().parent
CSV = TEST_DIR / 'data/test.csv'
MOCKED_DATETIME = datetime.datetime(2025, 3, 10, 10, 15, 0)
EXPECTED = [
    {'id': 1,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'https://example1.com',
     'attribute': 'nomination',
     'value': '1',
     'date': MOCKED_DATETIME},
    {'id': 2,
     'url_project_id': 1,
     'url_nominator_id': 1,
     'entity': 'https://example1.com',
     'attribute': 'surt',
     'value': 'http://(com,example1,)',
     'date': MOCKED_DATETIME},
    {'id': 3,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'https://example1.com',
     'attribute': 'List_Name',
     'value': 'file.txt',
     'date': MOCKED_DATETIME},
    {'id': 4,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'https://example1.com',
     'attribute': 'State',
     'value': 'Texas',
     'date': MOCKED_DATETIME},
    {'id': 5,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'http://example3.com',
     'attribute': 'nomination',
     'value': '1',
     'date': MOCKED_DATETIME},
    {'id': 6,
     'url_project_id': 1,
     'url_nominator_id': 1,
     'entity': 'http://example3.com',
     'attribute': 'surt',
     'value': 'http://(com,example3,)',
     'date': MOCKED_DATETIME},
    {'id': 7,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'http://example3.com',
     'attribute': 'List_Name',
     'value': 'file.txt',
     'date': MOCKED_DATETIME},
    {'id': 8,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'http://example3.com',
     'attribute': 'State',
     'value': 'Arkansas',
     'date': MOCKED_DATETIME},
    {'id': 9,
     'url_project_id': 1,
     'url_nominator_id': 2,
     'entity': 'http://example3.com',
     'attribute': 'List_Name',
     'value': 'file2.txt',
     'date': MOCKED_DATETIME}]


class TestCommandHandle():

    nominator = 12
    slug = 'project1'

    @patch('nomination.management.commands.fielded_batch_ingest.url_ingest')
    def test_command_handle_url_ingest(self, mocked_url_ingest):
        input_file = 'seeds.txt'
        call_command('fielded_batch_ingest',
                     input_file,
                     f'--nominator={self.nominator}',
                     f'--project={self.slug}',
                     '--verify')
        mocked_url_ingest.assert_called_once_with(input_file, self.nominator, self.slug, True)

    @patch('nomination.management.commands.fielded_batch_ingest.csv_ingest')
    def test_command_handle_csv_ingest(self, mocked_csv_ingest):
        input_file = 'seeds.csv'
        call_command('fielded_batch_ingest',
                     input_file,
                     f'--nominator={self.nominator}',
                     f'--project={self.slug}',
                     '--csv')
        mocked_csv_ingest.assert_called_once_with(input_file, self.nominator, self.slug, False)

    @patch('nomination.management.commands.fielded_batch_ingest.pydict_ingest')
    def test_command_handle_pydict_ingest(self, mocked_pydict_ingest):
        input_file = 'data.pkl'
        call_command('fielded_batch_ingest',
                     input_file,
                     f'--nominator={self.nominator}',
                     f'--project={self.slug}',
                     '--dict')
        mocked_pydict_ingest.assert_called_once_with(input_file, self.nominator, self.slug, False)


@pytest.mark.django_db
@patch('django.utils.timezone.now', Mock(return_value=MOCKED_DATETIME))
class TestCSVIngest():

    def test_csv_ingest(self, capsys):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()

        # load contents of test.csv, that is:
        # url,List_Name,State
        # https://example1.com,file.txt,Texas
        # http://example3.com,file.txt,Arkansas
        # http://example3.com,file2.txt,Arkansas

        call_command('fielded_batch_ingest',
                     CSV,
                     f'--nominator={nominator.id}',
                     f'--project={project.project_slug}',
                     '--csv')

        captured = capsys.readouterr()
        # Ingesting 2 unique URLs results in 2 new SURTs and 2 new nominations.
        # Other 5 attributes added for the 2 URLs are:
        # https://example1.com: (1) state of Texas, List_Name of (2) file.txt
        # http://example3.com: (3) state of Arkansas, List_Name of (4) file1.txt and (5) file2.txt
        assert captured.out == ('Created 2 new SURT entries.\n'
                                'Created 2 new nomination entries.\n'
                                'Created 5 other attribute entries.\n')
        assert list(URL.objects.all().values()) == EXPECTED

    def test_csv_ingest_reingest_does_nothing(self, capsys):
        """Verify running the same file a second time does nothing."""
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()

        call_command('fielded_batch_ingest',
                     CSV,
                     f'--nominator={nominator.id}',
                     f'--project={project.project_slug}',
                     '--csv')

        captured = capsys.readouterr()
        assert captured.out == ('Created 2 new SURT entries.\n'
                                'Created 2 new nomination entries.\n'
                                'Created 5 other attribute entries.\n')

        # Run the command again with the same file, and verify nothing changes.
        call_command('fielded_batch_ingest',
                     CSV,
                     f'--nominator={nominator.id}',
                     f'--project={project.project_slug}',
                     '--csv')

        captured = capsys.readouterr()
        assert captured.out == ('Created 0 new SURT entries.\n'
                                'Created 0 new nomination entries.\n'
                                'Created 0 other attribute entries.\n')

        assert list(URL.objects.all().values()) == EXPECTED


@pytest.mark.django_db
class TestCreateURLEntryLessDB:

    @patch('django.utils.timezone.now', Mock(return_value=MOCKED_DATETIME))
    @patch('nomination.management.commands.fielded_batch_ingest.surts_set', set())
    def test_create_url_entry_less_db_creates_surt(self):
        """Verify we create a SURT entry for a newly-nominated URL."""
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        url = 'https://example1.com'
        attribute = 'surt'
        value = 'http://(com,example1,)'
        result = fielded_batch_ingest.create_url_entry_less_db(project,
                                                               nominator,
                                                               url,
                                                               attribute,
                                                               value)
        assert result
        assert list(URL.objects.all().values()) == [{'id': 1,
                                                     'url_project_id': project.id,
                                                     'url_nominator_id': nominator.id,
                                                     'entity': url,
                                                     'attribute': attribute,
                                                     'value': value,
                                                     'date': MOCKED_DATETIME}]
        assert fielded_batch_ingest.surts_set == {url}

    @patch('nomination.management.commands.fielded_batch_ingest.surts_set',
           {'https://example1.com'})
    def test_create_url_entry_less_db_surt_exists(self):
        """Verify we don't create another SURT for an already-nominated URL."""
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        url = 'https://example1.com'
        attribute = 'surt'
        value = 'http://(com,example1,)'
        result = fielded_batch_ingest.create_url_entry_less_db(project,
                                                               nominator,
                                                               url,
                                                               attribute,
                                                               value)
        assert not result

    @patch('django.utils.timezone.now', Mock(return_value=MOCKED_DATETIME))
    def test_create_url_entry_less_db_non_surt_new_nomination(self):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        url = 'https://example4.com'
        attribute = 'nomination'
        value = '1'
        result = fielded_batch_ingest.create_url_entry_less_db(project,
                                                               nominator,
                                                               url,
                                                               attribute,
                                                               value)
        assert result
        assert list(URL.objects.all().values()) == [{'id': 1,
                                                     'url_project_id': project.id,
                                                     'url_nominator_id': nominator.id,
                                                     'entity': url,
                                                     'attribute': attribute,
                                                     'value': value,
                                                     'date': MOCKED_DATETIME}]
        assert f'{url}{attribute}{value}' in fielded_batch_ingest.nominator_urls_set

    @patch('django.utils.timezone.now', Mock(return_value=MOCKED_DATETIME))
    @patch('nomination.management.commands.fielded_batch_ingest.nominator_urls_set',
           {'https://example4.comnomination1'})
    def test_create_url_entry_less_db_non_surt_duplicate_nomination(self):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        # Nomination appears to be a duplicate, so don't create a nomination.
        result = fielded_batch_ingest.create_url_entry_less_db(project,
                                                               nominator,
                                                               'https://example4.com',
                                                               'nomination',
                                                               '1')
        assert not result

    @patch('nomination.models.URL.objects.create', side_effect=IntegrityError())
    def test_create_url_entry_less_db_raises_IntegrityError(self, mocked_create, capsys):
        project = factories.ProjectFactory()
        nominator = factories.NominatorFactory()
        url = 'https://example5.com'
        attribute = 'nomination'
        value = '1'
        result = fielded_batch_ingest.create_url_entry_less_db(project,
                                                               nominator,
                                                               url,
                                                               attribute,
                                                               value)
        assert not result
        captured = capsys.readouterr()
        assert captured.out == (f'Failed to create a new entry for url: {url} '
                                f'attribute: {attribute} value: {value}\n')
        mocked_create.assert_called_once_with(url_project=project, url_nominator=nominator,
                                              entity=url, attribute=attribute, value=value)


class TestURLFormatter:

    test_data = [
        (' www.example.com ', 'http://www.example.com'),
        ('http://www.example.com/pdfs/a file.pdf', 'http://www.example.com/pdfs/a%20file.pdf'),
        ('https://www.example.com/', 'https://www.example.com'),
    ]

    @pytest.mark.parametrize('input_url,output_url', test_data)
    def test_url_formatter(self, input_url, output_url):
        assert fielded_batch_ingest.url_formatter(input_url) == output_url
