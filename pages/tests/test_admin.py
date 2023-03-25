"""A single test file to test admin pages for all models in our project"""

from collections.abc import Callable
from http import HTTPStatus
from typing import Any

from django.contrib.admin.sites import AdminSite, all_sites
from django.contrib.auth import get_user_model
from django.db.models import Model
from django.test import TestCase
from django.urls import reverse

from parameterized import param, parameterized

from users.factories import SuperuserFactory

User = get_user_model()


def name_test(func: Callable[..., Any], param_num: int, param: param) -> str:
    """Helper method to name parametrized tests with admin model names"""

    site = param.args[0]
    model_admin = param.args[2]
    return f"{func.__name__}_{site.name}_{str(model_admin).replace('.', '_')}"


# Common decorator to parametrized tests with all admin models
each_model_admin = parameterized.expand(
    [
        (site, model, model_admin)
        for site in all_sites
        for model, model_admin in site._registry.items()
    ],
    name_func=name_test,
)


class ModelAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        """
        Setup super user for the test suite.
        Since super user have all permissions she should be able to access all admin pages.
        """

        cls.user = SuperuserFactory()

    def setUp(self) -> None:
        # Make sure super user is logged in to admin before each run
        return self.client.force_login(self.user)

    def make_url(self, site: AdminSite, model: type[Model], page: str) -> str:
        """Helper method to build a view url for any model registered in admin"""

        return reverse(
            f"{site.name}:{model._meta.app_label}_{model._meta.model_name}_{page}"
        )

    @each_model_admin
    def test_changelist(self, site, model, model_admin):
        """
        Test change (update) model view is accessible for each model class in admin.
        """

        url = self.make_url(site, model, "changelist")
        # pass search query parameter to simulate search in admin
        response = self.client.get(url, {"q": "example.com"})

        self.assertEqual(response.status_code, HTTPStatus.OK)

    @each_model_admin
    def test_add(self, site, model, model_admin):
        """
        Test add (create) model view is accessible for each model class in admin.
        """

        url = self.make_url(site, model, "add")
        response = self.client.get(url)

        # Some admin classes disallow add
        self.assertIn(response.status_code, (HTTPStatus.OK, HTTPStatus.FORBIDDEN))
