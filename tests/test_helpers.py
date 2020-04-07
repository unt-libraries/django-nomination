import json

import pytest

from nomination import views, models
from . import factories


pytestmark = pytest.mark.django_db


class TestGetProjectUrlCount():

    def test_returns_surt_count(self):
        factories.SURTFactory.create_batch(10)
        # Additional URL objects (SURTs are URL objects with their 'attribute'
        # attribute set to 'surt') should not affect the project URL count since
        # the count only looks for SURTs.
        factories.URLFactory.create_batch(5)
        url_query_set = models.URL.objects.all()
        result = views.get_project_url_count(url_query_set)

        assert result == 10


class TestGetProjectNominatorCount():

    def test_returns_nominator_count(self):
        factories.NominatedURLFactory.create_batch(10, value=1)
        # Other URLs that have not been nominated should not affect the
        # nominator count.
        factories.URLFactory.create_batch(5)
        url_query_set = models.URL.objects.all()
        result = views.get_project_nominator_count(url_query_set)

        assert result == 10

    def test_does_not_count_duplicates(self):
        nominator = factories.NominatorFactory()
        factories.NominatedURLFactory.create_batch(5, value=1, url_nominator=nominator)
        url_query_set = models.URL.objects.all()
        result = views.get_project_nominator_count(url_query_set)

        assert result == 1


class TestGetLookAhead():

    def test_returns_all_nominator_institutions(self):
        project = factories.ProjectFactory()
        expected = [
            url.url_nominator.nominator_institution
            for url in factories.URLFactory.create_batch(10, url_project=project)
        ]
        # Should not affect the institution list since these URLs are not
        # associated with the project.
        factories.URLFactory.create_batch(5)
        results = views.get_look_ahead(project)

        assert json.loads(results) == sorted(expected)

    def test_does_not_count_duplicates(self):
        project = factories.ProjectFactory()
        factories.URLFactory.create_batch(
            5,
            url_project=project,
            url_nominator__nominator_institution='UNT'
        )
        results = views.get_look_ahead(project)

        assert len(json.loads(results)) == 1
