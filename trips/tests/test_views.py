from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus

from django.contrib.messages import get_messages
from django.http import QueryDict
from django.test import TestCase
from django.urls import resolve, reverse_lazy
from django.utils import timezone

from dateutil import rrule

from companies.factories import CompanyFactory, SeatChartFactory
from trips.factories import (
    LocationFactory,
    RouteFactory,
    SeatFactory,
    SeatWithPassengerFactory,
    StopFactory,
    TripFactory,
    TripPastFactory,
    TripTomorrowFactory,
)
from trips.forms import RecurrenceForm
from trips.models import Seat, Trip
from trips.views import (
    CompanyRouteDetailView,
    CompanyRouteListView,
    CompanyTripDetailView,
    CompanyTripListView,
    LocationDetailView,
    LocationListView,
    RecurrenceView,
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


class LocationListViewTests(TestCase):
    """
    Test suite for location list view.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        cls.locations = LocationFactory.create_batch(size=3)
        cls.url = reverse_lazy("locations:location-list")
        cls.template_name = "trips/location_list.html"

    def test_location_list_url_resolves_correct_view(self):
        view = resolve(self.url)

        self.assertEqual(view.func.__name__, LocationListView.as_view().__name__)

    def test_location_list_view_works(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "All Locations")
        self.assertNotContains(response, "Hi I should not be on this page")
        self.assertIn("locations", response.context)

        # Make sure all locations are listed
        self.assertEqual(len(response.context["locations"]), len(self.locations))


class LocationDetailViewTests(TestCase):
    """
    Test suite for viewing the detail page of any location.
    """

    @classmethod
    def setUpTestData(cls):
        cls.location = LocationFactory()
        cls.url = cls.location.get_absolute_url()  # type:ignore
        cls.template_name = "trips/location_detail.html"

    def test_location_detail_view_works_correctly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.location.name)
        self.assertNotContains(response, "Hi I should not be on this page")

    def test_location_detail_url_resolves_correct_view(self):
        view = resolve(self.url)

        self.assertEqual(view.func.__name__, LocationDetailView.as_view().__name__)

    def test_anonymous_user_can_access_location_detail_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.location.name)
        self.assertNotContains(response, "Hi I should not be on this page")


# Public Views
class TripListViewTests(TestCase):
    """
    Test suite for trip list view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.trip = TripFactory()
        cls.url = reverse_lazy("trips:trip-list")
        cls.redirect_url = reverse_lazy("pages:home")
        cls.template_name = "trips/trip_list.html"
        cls.origin = LocationFactory(name="Buenos Aires")
        cls.destination = LocationFactory(name="Mendoza")

    @classmethod
    def build_url(cls, **kwargs):
        """
        Helper method to add query parameters to a url
        """

        q = QueryDict("", mutable=True)
        q.update(**kwargs)
        return "%s?%s" % (cls.url, q.urlencode())

    def test_trip_list_works_for_anonymous_user(self):
        url = self.build_url(
            trip_type="round_trip",
            num_of_passengers=1,
            origin="Buenos Aires",
            destination="Mendoza",
            departure=timezone.now().strftime("%d-%m-%Y"),
        )
        self.response = self.client.get(url)

        self.assertEqual(self.response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(self.response, self.template_name)
        self.assertContains(self.response, "Results")
        self.assertNotContains(self.response, "Hi there. I should not be on this page.")

    def test_trip_list_redirects_to_home_with_message_for_empty_query(self):
        """
        Here we don't pass the query params at all!
        Just hit the endpoint /trips/ and this should redirect
        """

        url = self.build_url()
        response = self.client.get(url)

        self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

    def test_trip_list_redirects_to_home_with_message_for_invalid_origin(self):
        url = self.build_url(
            trip_type="round_trip",
            num_of_passengers=1,
            origin="BsAs",  # <- invalid location name
            destination="Mendoza",
            departure=timezone.now().strftime("%d-%m-%Y"),
        )
        response = self.client.get(url)

        self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

    def test_trip_list_redirects_to_home_with_message_for_invalid_destination(self):
        url = self.build_url(
            trip_type="round_trip",
            num_of_passengers=1,
            origin="Buenos Aires",
            destination="India",  # <- invalid destination
            departure=timezone.now().strftime("%d-%m-%Y"),
        )

        response = self.client.get(url)

        self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

    def test_trip_list_redirects_to_home_with_message_for_invalid_departure_date(self):
        yesterday = (timezone.now() - timedelta(days=1)).strftime("%d-%m-%Y")

        url = self.build_url(
            trip_type="round_trip",
            num_of_passengers=1,
            origin="Buenos Aires",
            destination="Mendoza",
            departure=yesterday,  # <- invalid departure date
        )

        response = self.client.get(url)

        self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

    def test_trip_list_redirects_to_home_with_message_for_invalid_return_date(self):
        today = timezone.now()
        departure = today.strftime("%d-%m-%Y")
        return_date = (today - timedelta(days=1)).strftime("%d-%m-%Y")

        url = self.build_url(
            trip_type="round_trip",
            num_of_passengers=1,
            origin="Buenos Aires",
            destination="Mendoza",
            departure=departure,
        )
        url += f"&return={return_date}"

        response = self.client.get(url)

        self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

    def test_trip_list_redirects_to_home_with_message_for_invalid_num_of_passengers(
        self,
    ):
        today = timezone.now()
        departure = today.strftime("%d-%m-%Y")

        def assert_invalid(url, self):
            response = self.client.get(url)

            self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
            self.assertTemplateNotUsed(response, self.template_name)

            messages = list(get_messages(response.wsgi_request))

            self.assertEqual(len(messages), 1)
            self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

        url_1 = self.build_url(
            trip_type="round_trip",
            num_of_passengers=0,  # <- invalid
            origin="Buenos Aires",
            destination="Mendoza",
            departure=departure,
        )
        url_2 = self.build_url(
            trip_type="round_trip",
            num_of_passengers=11,  # <- invalid
            origin="Buenos Aires",
            destination="Mendoza",
            departure=departure,
        )

        assert_invalid(url=url_1, self=self)
        assert_invalid(url=url_2, self=self)

    def test_trip_list_redirects_to_home_with_message_for_invalid_trip_type(
        self,
    ):
        today = timezone.now()
        departure = today.strftime("%d-%m-%Y")

        def assert_invalid(url, self):
            response = self.client.get(url)

            self.assertRedirects(response, self.redirect_url, HTTPStatus.FOUND)
            self.assertTemplateNotUsed(response, self.template_name)

            messages = list(get_messages(response.wsgi_request))

            self.assertEqual(len(messages), 1)
            self.assertIn(TripListView.invalid_query_msg, str(messages[0]))

        url_1 = self.build_url(
            trip_type="",  # <- invalid
            num_of_passengers=1,
            origin="Buenos Aires",
            destination="Mendoza",
            departure=departure,
        )
        url_2 = self.build_url(
            trip_type="solo",  # <- invalid
            num_of_passengers=1,
            origin="Buenos Aires",
            destination="Mendoza",
            departure=departure,
        )

        assert_invalid(url=url_1, self=self)
        assert_invalid(url=url_2, self=self)

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
        cls.seatchart = SeatChartFactory(company=cls.company)

        cls.login_url = reverse_lazy("account_login")
        cls.permission = "trips.add_trip"
        cls.template_name = "trips/trip_form.html"
        cls.url = reverse_lazy("companies:trip-create", args=[str(cls.company.slug)])

        cls.now = timezone.now()
        cls.tomorrow = cls.now + timedelta(days=1)
        cls.day_after = cls.now + timedelta(days=2)

    def get_seat_numbers(self, floor="lower") -> list:
        return self.seatchart.json.get(floor, {}).get("enabledSeats", [])

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

        # Arrange

        # Make sure no trip in DB
        self.assertEqual(Trip.objects.count(), 0)

        # Create two locations as trip needs their ids since they are foreign keys
        origin, destination = LocationFactory.create_batch(size=2)

        # Build post data
        # Make sure departure in future and arrival > departure
        departure = self.tomorrow.strftime("%Y-%m-%d %H:%m")
        arrival = self.day_after.strftime("%Y-%m-%d %H:%m")

        data = {
            "name": "Argentina Trip",
            "origin": str(origin.id),
            "destination": str(destination.id),
            "departure": departure,
            "arrival": arrival,
            "price": "10",
            "status": "A",
            "mode": "D",
            "image": "",
            "description": "My awesome Argentina Trip",
            "seatchart": self.seatchart.title,  # <- pass company seatchart
        }

        # ACT
        self.client.force_login(self.owner)

        # Creation will redirect to trip-detail so make `follow=True`
        response = self.client.post(path=self.url, data=data, follow=True)

        # Get trip created in DB
        trip = Trip.objects.first()
        expected_url = self.company.get_trip_list_url()

        # Verify redirection
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        # Verify Trip created in DB
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(trip.name, "Argentina Trip")
        self.assertEqual(trip.slug, "argentina-trip")
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

        # Verify seats for trip correctly created based on seatchart
        seat_numbers = self.get_seat_numbers("lower") + self.get_seat_numbers("upper")
        seats_from_db = list(trip.seats.values_list("seat_number", flat=True))

        self.assertEqual(trip.seats.count(), len(seat_numbers))
        self.assertEqual(seats_from_db, seat_numbers)


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

    def test_company_trip_detail_view_is_accessible_by_company_owner(self):
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


class RecurrenceViewTests(TestCase):
    """
    Test suite for the recurrence view.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.trip = TripTomorrowFactory(company=cls.company)
        cls.seat = SeatFactory(trip=cls.trip, seat_status=Seat.AVAILABLE)
        cls.login_url = reverse_lazy("account_login")
        cls.url = reverse_lazy(
            "companies:trip-recurrence",
            kwargs={"slug": cls.company.slug, "id": str(cls.trip.id)},
        )
        cls.template_name = "trips/recurrence_form.html"

    def test_recurrence_url_resolves_recurrence_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, RecurrenceView.as_view().__name__)

    def test_recurrence_view_is_not_accessible_by_anonymous_user(self):
        """Here an anonymous user is routed to login url"""

        response = self.client.get(self.url)
        redirect_url = f"{self.login_url}?next={self.url}"

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_url, HTTPStatus.FOUND)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_recurrence_view_is_not_accessible_by_normal_public_user(self):
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

    def test_recurrence_view_is_not_accessible_by_another_company_owner(self):
        owner = CompanyOwnerFactory()
        self.client.force_login(owner)  # type:ignore

        response = self.client.get(self.url)

        # Assert user is not staff | superuser and correctly authenticated
        self.assertFalse(owner.is_staff)
        self.assertFalse(owner.is_superuser)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Assert user is forbidden access
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTemplateNotUsed(response, self.template_name)

    def test_recurrence_view_is_not_accessible_by_staffuser(self):
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

    def test_recurrence_view_is_accessible_by_company_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.url)
        form = response.context["form"]

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Recurrence")
        self.assertNotContains(response, "Hi I should not be on this page!")
        self.assertIsInstance(form, RecurrenceForm)

    def test_recurrence_view_works_on_successful_post(self):
        """
        This is an end-to-end kind of test for trip recurrence creation.
        """

        # First make sure only trip in DB
        self.assertEqual(Trip.objects.count(), 1)

        # Build post data
        tomorrow = timezone.now() + timedelta(days=1)
        count = 4
        data = {
            "dtstart": tomorrow,
            "count": count,
            "freq": rrule.DAILY,
        }

        self.client.force_login(self.owner)  # type:ignore

        # Creation will redirect to trip-list so make `follow=True`
        response = self.client.post(path=self.url, data=data, follow=True)

        expected_url = self.company.get_trip_list_url()  # type:ignore

        # Verify redirection
        self.assertRedirects(
            response=response,
            expected_url=expected_url,
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

        # Recurrence trips should have been created. Verify them...
        self.assertEqual(Trip.objects.count(), count + 1)

        # Pull latest trip and check all attributes are equal
        trip_from_db = Trip.objects.last()
        self.assertEqual(trip_from_db.name, self.trip.name)
        self.assertEqual(trip_from_db.price, self.trip.price)
        self.assertEqual(trip_from_db.description, self.trip.description)
        self.assertEqual(trip_from_db.duration, self.trip.duration)

        # However departure should not match
        self.assertNotEqual(trip_from_db.departure, self.trip.departure)

        # Verify content of final redirected page
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Verify recurrence creation success messages on final page.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 2)
        self.assertEqual(str(messages[0]), f"Total Occurrences: {count}")
        self.assertEqual(str(messages[1]), RecurrenceView.success_message)


class CompanyRouteListViewTests(TestCase):
    """Test suite for the company admin route list view"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.route = RouteFactory(company=cls.company)
        cls.url = cls.company.get_route_list_url()
        cls.template_name = "trips/company_route_list.html"

    def test_company_route_list_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyRouteListView.as_view().__name__)

    def test_company_route_list_view_works(self):
        # Make the company owner login to the platform
        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, "Routes")
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert valid context
        routes = response.context["routes"]
        self.assertEqual(len(routes), 1)

        # Assert company itself in context
        self.assertEqual(self.company, response.context["company"])


class CompanyRouteDetailViewTests(TestCase):
    """Test suite for the company route detail view"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = CompanyOwnerFactory()
        cls.company = CompanyFactory(owner=cls.owner)
        cls.route = RouteFactory(company=cls.company)
        cls.stops = StopFactory.create_batch(size=5, route=cls.route)
        cls.url = cls.route.get_admin_url()
        cls.template_name = CompanyRouteDetailView.template_name

    def test_company_route_detail_url_resolves_correct_view(self):
        view = resolve(self.url)
        self.assertEqual(view.func.__name__, CompanyRouteDetailView.as_view().__name__)

    def test_company_route_detail_view_works(self):
        # Make the company owner login to the platform
        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        # Assert user is correctly authenticated and neither superuser nor staff
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.owner, self.company.owner)

        # Assert user is given access
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertContains(response, self.route.name)
        self.assertNotContains(response, "Hi I should not be on this page!")

        # Assert valid context
        route = response.context["route"]
        stops = response.context["stops"]

        self.assertEqual(route, self.route)
        self.assertEqual(list(stops), self.stops)
        self.assertEqual(len(stops), 5)

        # Assert company itself in context
        self.assertEqual(self.company, response.context["company"])
