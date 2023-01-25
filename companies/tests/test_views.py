from http import HTTPStatus

from django.test import TestCase
from django.urls import resolve, reverse

from companies.factories import CompanyFactory
from companies.views import CompanyDetailView, CompanyListView
from users.factories import UserFactory


class CompanyListTests(TestCase):
    """Test suite for company list view"""

    def setUp(self):
        self.url = reverse("companies:company_list")
        self.template_name = "companies/company_list.html"
        self.response = self.client.get(self.url)

    def test_company_list_view_works(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, "companies")
        self.assertNotContains(self.response, "Hi I should not be on this page")

    def test_company_list_url_resolves_companylistview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyListView.as_view().__name__)

    def test_company_list_view_show_relevant_message_for_no_data(self):
        self.assertContains(self.response, "There are no companies yet.")

    def test_company_list_view_shows_all_companies(self):
        company_1, company_2 = CompanyFactory.create_batch(2)

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["companies"]), 2)
        self.assertContains(response, company_1.name)
        self.assertContains(response, company_2.name)


class CompanyDetailViewTests(TestCase):
    def setUp(self):
        self.company = CompanyFactory()
        self.url = self.company.get_absolute_url()
        self.template_name = "companies/company_detail.html"
        self.response = self.client.get(self.url)

    def test_company_detail_view_works_correctly(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, self.company.name)
        self.assertContains(self.response, self.company.description)
        self.assertNotContains(self.response, "Hi I should not be on this page")

    def test_company_detail_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyDetailView.as_view().__name__)

    def test_anonymous_user_can_access_company_detail_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.company.name)

    def test_logged_in_user_can_access_company_detail_view(self):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.company.name)
