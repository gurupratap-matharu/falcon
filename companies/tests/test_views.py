from http import HTTPStatus

from django.test import TestCase
from django.urls import resolve, reverse_lazy

from companies.factories import CompanyFactory, SeatChartFactory
from companies.models import Company, SeatChart
from companies.views import (
    CompanyBookView,
    CompanyDashboardView,
    CompanyDetailView,
    CompanyListView,
    LiveStatusView,
    SeatChartDetailView,
    SeatChartListView,
)
from users.factories import (
    CompanyOwnerFactory,
    StaffuserFactory,
    SuperuserFactory,
    UserFactory,
)


class CompanyListTests(TestCase):
    """Test suite for company list view"""

    def setUp(self):
        self.url = reverse_lazy("companies:company_list")
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


class CompanyBookViewTests(TestCase):
    """
    Test suite for dedicated company ticket booking view.
    """

    def setUp(self):
        self.company = CompanyFactory()
        self.url = reverse_lazy("companies:company-book", args=[str(self.company.slug)])
        self.template_name = "companies/company_book.html"

    def test_company_book_view_is_accessible(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertIn("company", response.context)
        self.assertContains(response, self.company.name)
        self.assertContains(response, self.company.slug)
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_book_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyBookView.as_view().__name__)


class CompanyDashboardTests(TestCase):
    """Test suite for the company dashboard page view"""

    def setUp(self):
        self.owner = CompanyOwnerFactory()
        self.company = CompanyFactory(owner=self.owner)
        self.login_url = reverse_lazy("account_login")
        self.url = reverse_lazy("companies:dashboard", args=[str(self.company.slug)])
        self.template_name = "companies/dashboard.html"

    def test_company_dashboard_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyDashboardView.as_view().__name__)

    def test_company_dashboard_view_is_not_accessible_by_anonymous_user(self):
        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_dashboard_view_is_not_accessible_by_logged_in_normal_public_user(
        self,
    ):
        user = UserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_dashboard_view_is_not_accessible_by_another_company_owner(self):
        """
        Company B owner should not be able to access the dashboard for Company A
        """
        # Create another company owner and log her in
        user = CompanyOwnerFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_dashboard_view_is_accessible_by_superuser(self):
        user = SuperuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff | superuser and correctly authenticated
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Dashboard")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_dashboard_view_is_not_accessible_by_staffuser(self):
        user = StaffuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff but not superuser and correctly authenticated
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert staff user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_dashboard_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the dashboard."""

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, self.company)
        self.assertEqual(self.company, response.context["company"])
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Test kpi in context
        self.assertIn("kpis", response.context)
        self.assertIsInstance(response.context["kpis"], dict)


class SeatChartListTests(TestCase):
    """
    Test suite for seat chart list view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.seatchart = SeatChartFactory.create_batch(size=3, company=cls.company)
        cls.template_name = "companies/seatchart_list.html"
        cls.url = reverse_lazy("companies:seatchart-list", args=[cls.company.slug])
        cls.login_url = reverse_lazy("account_login")

    def test_seatchart_list_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, SeatChartListView.as_view().__name__)

    def test_company_seatchart_list_view_redirects_to_login_for_anonymous_user(self):
        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_seatchart_list_view_is_not_accessible_by_logged_in_normal_public_user(
        self,
    ):
        user = UserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_seatchart_list_view_is_not_accessible_by_another_company_owner(
        self,
    ):
        """
        Company B owner should not be able to access the seatcharts for Company A
        """
        # Create another company owner and log her in
        user = CompanyOwnerFactory()
        self.client.force_login(user)  # type:ignore

        # Make company B owner try to access company A seatchart list view
        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_seatchart_list_view_is_not_accessible_by_staffuser(self):
        user = StaffuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff but not superuser and correctly authenticated
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert staff user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_seatchart_list_view_is_accessible_by_superuser(self):
        user = SuperuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff | superuser and correctly authenticated
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "SeatCharts")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_seatchart_list_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the seatchart list view."""

        user = self.owner
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "SeatCharts")
        self.assertContains(response, self.company)
        self.assertEqual(self.company, response.context["company"])
        self.assertNotContains(response, "Hi I should not be on this page!")


class SeatChartDetailTests(TestCase):
    """
    Test suite for seatchart detail view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.seatchart = SeatChartFactory(company=cls.company)
        cls.template_name = "companies/seatchart_detail.html"
        cls.url = reverse_lazy(
            "companies:seatchart-detail", args=[cls.company.slug, str(cls.seatchart.id)]
        )
        cls.login_url = reverse_lazy("account_login")

    def test_setup_data_is_correctly_generated(self):
        company_from_db = Company.objects.first()
        seatchart_from_db = SeatChart.objects.first()

        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(SeatChart.objects.count(), 1)
        self.assertEqual(seatchart_from_db.company, company_from_db)

    def test_seatchart_detail_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, SeatChartDetailView.as_view().__name__)

    def test_seatchart_detail_view_redirects_to_login_for_anonymous_user(self):
        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_seatchart_detail_view_is_not_accessible_by_logged_in_normal_public_user(
        self,
    ):
        user = UserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_seatchart_detail_view_is_not_accessible_by_another_company_owner(
        self,
    ):
        """
        Company B owner should not be able to access the seatcharts for Company A
        """
        # Create another company owner and log her in
        user = CompanyOwnerFactory()
        self.client.force_login(user)  # type:ignore

        # Make company B owner try to access company A seatchart detail view
        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_seatchart_detail_view_is_not_accessible_by_staffuser(self):
        user = StaffuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff but not superuser and correctly authenticated
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert staff user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_seatchart_detail_view_is_accessible_by_superuser(self):
        user = SuperuserFactory()
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is staff | superuser and correctly authenticated
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.seatchart.title)
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_seatchart_detail_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the seatchart detail view."""

        user = self.owner
        self.client.force_login(user)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.seatchart.title)
        self.assertContains(response, self.company)
        self.assertEqual(self.company, response.context["company"])
        self.assertNotContains(response, "Hi I should not be on this page!")


class LiveStatusViewTests(TestCase):
    """
    Test suite for live GPS map view
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.url = reverse_lazy("companies:live-status", args=[cls.company.slug])

    def test_live_status_url_resolves_correct_view(self):
        view = resolve(self.url)

        self.assertEqual(view.func.__name__, LiveStatusView.as_view().__name__)

    # TODO WRITE PERMISSION TESTS
