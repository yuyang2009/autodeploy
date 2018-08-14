from django.test import TestCase
import pytest


pytestmark = pytest.mark.django_db


def test_environment_get_absolute_url(environment):
    assert environment.get_absolute_url() == f"/environment_page/{environment.id}/"
