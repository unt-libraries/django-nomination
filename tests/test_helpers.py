import json

from django.http import Http404
import pytest

from nomination import views, models
import factories


pytestmark = pytest.mark.django_db


class TestGetProject():

    def test_returns_project(self):
        project = factories.ProjectFactory()
        result = views.get_project(project.project_slug)
        assert result == project

    def test_raises_404(self):
        with pytest.raises(Http404):
            views.get_project('fake_project')


class TestGetProjectUrlCount():

    def test_returns_surt_count(self):
        factories.SURTFactory.create_batch(10)
        # Should not affect the surt count.
        factories.URLFactory.create_batch(5)
        url_query_set = models.URL.objects.all()
        result = views.get_project_url_count(url_query_set)

        assert result == 10


class TestGetProjectNominatorCount():

    def test_returns_nominator_count(self):
        factories.NominatedURLFactory.create_batch(10, value=1)
        # Should not affect nominator count.
        factories.SURTFactory.create_batch(5)
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
        # Should not affect the institution list.
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
