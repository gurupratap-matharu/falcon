from decimal import Decimal
from http import HTTPStatus

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import resolve, reverse_lazy

from companies.factories import CompanyFactory
from trips.factories import (
    LocationFactory,
    SeatFactory,
    SeatWithPassengerFactory,
    TripFactory,
    TripPastFactory,
    TripTomorrowFactory,
)
from trips.models import Seat, Trip
from trips.views import (
    CompanyTripDetailView,
    CompanyTripListView,
    TripCreateView,
    TripDetailView,
    TripListView,
    TripPassengerPdfView,
    TripUpdateView,
)
from users.factories import (
    CompanyOwnerFactory,
    StaffuserFactory,
    SuperuserFactory,
    UserFactory,
)


# Public Views
class TripListViewTests(TestCase):
    """
    Test suite for trip list view.
    """

    def setUp(self):
        self.url = reverse_lazy("trips:trip-list")
        self.response = self.client.get(self.url)
        self.template_name = "trips/trip_list.html"

    def test_trip_list_works_for_anonymous_user(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, "Results")
        self.assertNotContains(self.response, "Hi there. I should not be on this page.")

    def test_trip_list_url_resolve_triplistview(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripListView.as_view().__name__)


class TripDetailViewTests(TestCase):
    """Test Suite for Trip DetailView"""

    @classmethod
    def setUpTestData(cls):
        cls.trip = TripFactory()
        cls.url = cls.trip.get_absolute_url()
        cls.template_name = "trips/trip_detail.html"

    def setUp(self) -> None:
        self.response = self.client.get(self.url)

    def test_trip_detail_view_works_correctly(self):
        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, self.trip.origin)
        self.assertContains(self.response, self.trip.destination)
        self.assertNotContains(self.response, "Hi I should not be on this page")

    def test_trip_detail_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripDetailView.as_view().__name__)

    def test_anonymous_user_can_access_trip_detail_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

    def test_logged_in_user_can_access_trip_detail_view(self):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)


# Private Views
class TripCreateViewTests(TestCase):
    """Test suite for the trip create view"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.login_url = reverse_lazy("account_login")
        cls.url = reverse_lazy("companies:trip-create", args=[str(cls.company.slug)])
        cls.template_name = "trips/trip_form.html"
        cls.permission = "trips.add_trip"

    def test_company_trip_create_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripCreateView.as_view().__name__)

    def test_company_trip_create_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_create_view_is_not_accessible_by_logged_in_normal_public_user(
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

    def test_company_trip_create_view_is_not_accessible_by_another_company_owner(
        self,
    ):
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

    def test_company_trip_create_view_is_not_accessible_by_staffuser(self):
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

    def test_company_trip_create_view_is_accessible_by_superuser(self):
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
        self.assertContains(response, "Create")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_trip_create_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the trip create page."""

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Create")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_trip_create_view_works_on_successful_post(self):
        """
        This is an end-to-end kind of test for trip creation.
        """

        # Create two locations as trip needs their ids since they are foreign keys
        origin, destination = LocationFactory.create_batch(size=2)
        # Build data
        data = {
            "name": "Europe Trip",
            "origin": str(origin.id),
            "destination": str(destination.id),
            "departure": "2023-03-16 15:00",
            "arrival": "2023-03-31 16:00",
            "price": "1",
            "status": "A",
            "mode": "D",
            "image": "",
            "description": "",
        }

        self.client.force_login(self.owner)  # type:ignore

        # Creation will redirect to trip-detail so make `follow=True`
        response = self.client.post(path=self.url, data=data, follow=True)

        # Get trip created in DB
        trip = Trip.objects.first()
        expected_url = self.company.get_trip_list_url()  # type:ignore

        # Verify redirection
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        # Verify DB count and content
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(trip.name, "Europe Trip")
        self.assertEqual(trip.slug, "europe-trip")
        self.assertEqual(trip.origin, origin)
        self.assertEqual(trip.destination, destination)
        self.assertEqual(trip.status, "A")
        self.assertEqual(trip.mode, "D")

        # Verify content of final redirected page
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Verify trip creation success message on final page.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), TripCreateView.success_message)


class TripUpdateViewTests(TestCase):
    """Test suite for trip update view in company admin interface"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.trip = TripTomorrowFactory(company=cls.company)
        cls.seat = SeatFactory(trip=cls.trip, seat_status=Seat.AVAILABLE)
        cls.login_url = reverse_lazy("account_login")
        cls.url = reverse_lazy(
            "companies:trip-update",
            kwargs={"slug": cls.company.slug, "id": str(cls.trip.id)},
        )
        cls.template_name = "trips/trip_form.html"
        cls.permission = "trips.change_trip"

    def test_trip_update_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripUpdateView.as_view().__name__)

    def test_trip_update_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_trip_upate_view_is_not_accessible_by_logged_in_normal_public_user(
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

    def test_trip_upate_view_is_not_accessible_by_another_company_owner(
        self,
    ):
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

    def test_trip_upate_view_is_not_accessible_by_staffuser(self):
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

    def test_trip_update_view_is_accessible_by_superuser(self):
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
        self.assertContains(response, "Update")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_trip_update_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access their own trip."""

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Create")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_trip_update_view_works_on_successful_post(self):
        """
        This is an end-to-end kind of test for trip updation.
        """

        # Build data
        data = {
            "name": "Antartica Trip",
            "origin": str(self.trip.origin.id),
            "destination": str(self.trip.destination.id),
            "departure": self.trip.departure.strftime("%Y-%m-%d %H:%M"),
            "arrival": self.trip.arrival.strftime("%Y-%m-%d %H:%M"),
            "price": "20",
            "status": "A",
            "mode": "D",
            "image": "",
            "description": "My new trip to Antartica",
        }

        self.client.force_login(self.owner)  # type:ignore

        # Creation will redirect to trip-detail so make `follow=True`
        response = self.client.post(path=self.url, data=data, follow=True)

        # Get trip created in DB
        trip = Trip.objects.first()
        expected_url = trip.get_passenger_list_url()  # type:ignore

        # Verify redirection
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        # Verify DB count and content
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(trip.name, "Antartica Trip")
        self.assertEqual(trip.price, Decimal(20))
        self.assertEqual(trip.description, "My new trip to Antartica")

        # Verify content of final redirected page
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Verify trip creation success message on final page.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), TripUpdateView.success_message)


class CompanyTripListViewTests(TestCase):
    """Test suite for company trip list view"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.trips = TripTomorrowFactory.create_batch(
            size=2, company=cls.company, status=Trip.ACTIVE
        )
        cls.inactive_trip = TripPastFactory(company=cls.company)
        # if you don't create seats veer you will get zero division error while
        # calculating occupancy and the tests will fail
        for trip in cls.trips:
            SeatFactory.reset_sequence(1)
            SeatFactory(trip=trip, seat_status=Seat.AVAILABLE)

        cls.url = cls.company.get_trip_list_url()  # type:ignore
        cls.template_name = "trips/company_trip_list.html"
        cls.permission = "trips.view_trip"
        cls.login_url = reverse_lazy("account_login")

    def test_company_trip_list_resolves_correct_view(self):
        view = resolve(self.url)

        self.assertEqual(view.func.__name__, CompanyTripListView.as_view().__name__)

    def test_company_trip_list_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_list_view_is_not_accessible_by_logged_in_normal_public_user(
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

    def test_company_trip_list_view_is_not_accessible_by_another_company_owner(
        self,
    ):
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

    def test_company_trip_list_view_is_not_accessible_by_staffuser(self):
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

    def test_company_trip_list_view_is_accessible_by_superuser(self):
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

    def test_company_trip_list_view_is_accessible_by_company_user(self):
        """Check if a company staff | owner can access the trip list page."""

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Create Trip")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert valid trips are shown
        trips = response.context["trips"]
        self.assertEqual(len(trips), 2)
        self.assertIn(self.trips[0], trips)
        self.assertIn(self.trips[1], trips)
        self.assertNotIn(self.inactive_trip, trips)

        # Assert company itself in context
        self.assertEqual(self.company, response.context["company"])


class CompanyTripDetailViewTests(TestCase):
    """Test suite for company trip detail that shows all passenger lists"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.trip = TripTomorrowFactory(company=cls.company)

        SeatFactory.reset_sequence(1)
        # Create two booked seats with a passenger assigned to it
        cls.booked_seats = SeatWithPassengerFactory.create_batch(size=2, trip=cls.trip)
        # Create two available empty seats
        cls.empty_seats = SeatFactory.create_batch(
            size=2, trip=cls.trip, seat_status=Seat.AVAILABLE
        )
        cls.seats = cls.booked_seats + cls.empty_seats

        cls.template_name = "trips/company_trip_detail.html"
        cls.permission = "trips.view_trip"
        cls.login_url = reverse_lazy("account_login")
        cls.url = reverse_lazy(
            "companies:trip-detail",
            kwargs={"slug": cls.company.slug, "id": str(cls.trip.id)},
        )

    def test_company_trip_detail_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyTripDetailView.as_view().__name__)

    def test_company_trip_detail_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_company_trip_detail_view_is_not_accessible_by_logged_in_normal_public_user(
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

    def test_company_trip_detail_view_is_not_accessible_by_another_company_owner(
        self,
    ):
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

    def test_company_trip_detail_view_is_not_accessible_by_staffuser(self):
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

    def test_company_trip_detail_view_is_accessible_by_superuser(self):
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
        self.assertContains(response, "Passengers")
        self.assertNotContains(response, "Hi I should not be on this page!")

    def test_company_trip_detail_view_is_accessible_by_company_user(self):
        """
        Check if a company staff | owner can access the trip detail page
        with all passenger information.
        """

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Passengers")
        self.assertContains(response, "Update Trip")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert context is correctly built
        company = response.context["company"]
        trip = response.context["trip"]

        self.assertEqual(company, self.company)
        self.assertEqual(trip, self.trip)

        # Assert all passengers are shown
        # TODO


class TripPassengerPdfViewTests(TestCase):
    """
    Test suite for generating pdf for all passengers in a trip

    Note Veer:
        - This view returns a pdf file for download.
        - So the tests are a bit different.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.trip = TripTomorrowFactory(company=cls.company)

        SeatFactory.reset_sequence(1)
        # Create two booked seats with a passenger assigned to it
        cls.booked_seats = SeatWithPassengerFactory.create_batch(size=2, trip=cls.trip)
        # Create two available empty seats
        cls.empty_seats = SeatFactory.create_batch(
            size=2, trip=cls.trip, seat_status=Seat.AVAILABLE
        )
        cls.seats = cls.booked_seats + cls.empty_seats

        cls.template_name = "trips/trip_passengers_pdf.html"
        cls.permission = "trips.view_trip"
        cls.login_url = reverse_lazy("account_login")
        cls.url = reverse_lazy(
            "companies:trip-passengers-pdf",
            kwargs={"slug": cls.company.slug, "id": str(cls.trip.id)},
        )

    def test_trip_passengers_pdf_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, TripPassengerPdfView.as_view().__name__)

    def test_trip_passengers_pdf_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_trip_passengers_pdf_view_is_not_accessible_by_logged_in_normal_public_user(
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

    def test_trip_passengers_pdf_view_is_not_accessible_by_another_company_owner(
        self,
    ):
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

    def test_trip_passengers_pdf_view_is_not_accessible_by_staffuser(self):
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

    def test_trip_passengers_pdf_view_is_accessible_by_superuser(self):
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

        # Assert PDF in response
        self.assertNotEqual(response.content, b"")
        self.assertEqual(
            response["content-disposition"], 'attachment;filename="passengers.pdf"'
        )
        self.assertEqual(response["content-type"], "application/pdf")

        # Assert context is correctly built
        company = response.context["company"]
        trip = response.context["trip"]

        self.assertEqual(company, self.company)
        self.assertEqual(trip, self.trip)

    def test_trip_passengers_pdf_view_is_accessible_by_company_user(self):
        """
        Check if a company staff | owner can access the trip detail page
        with all passenger information.
        """

        self.client.force_login(self.owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)

        # Assert PDF in response
        self.assertNotEqual(response.content, b"")
        self.assertEqual(
            response["content-disposition"], 'attachment;filename="passengers.pdf"'
        )
        self.assertEqual(response["content-type"], "application/pdf")

        # Assert context is correctly built
        company = response.context["company"]
        trip = response.context["trip"]

        self.assertEqual(company, self.company)
        self.assertEqual(trip, self.trip)

        # TODO Assert all passengers are shown
        # Here we are not yet checking the content of the pdf itself. Maybe the <tr>
        # count is same the number of passengers in a trip!

    def test_trip_passengers_pdf_view_is_not_accessible_by_another_company_user(
        self,
    ):
        """
        Check whether a staff user from one company cannot access passenger list
        of another company
        """

        # Create a random company and its owner
        random_owner = CompanyOwnerFactory()
        _ = CompanyFactory(owner=random_owner)

        # Make it login to our platform
        self.client.force_login(random_owner)  # type:ignore

        # Random owner is trying to access our main company passenger list
        # This should not be allowed
        response = self.client.get(self.url)

        # Assert random_owner is not staff | superuser and correctly authenticated
        self.assertFalse(random_owner.is_staff)
        self.assertFalse(random_owner.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert random_owner is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)
