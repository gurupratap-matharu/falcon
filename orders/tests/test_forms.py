from django.test import SimpleTestCase, TestCase

from django_countries import countries
from faker import Faker

from orders.forms import OrderForm, OrderSearchForm, PassengerForm
from orders.models import Passenger

fake = Faker()


class OrderFormTests(SimpleTestCase):
    """Test suite for order model form"""

    def setUp(self):
        self.field_required_msg = "This field is required."
        self.form_data = {
            "name": "Gisela Vidal",
            "email": "giselavidalgv@email.com",
            "residence": "AR",
        }

    def test_order_form_is_valid_for_valid_data(self):
        form = OrderForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_empty_order_form_raises_valid_errors(self):
        form = OrderForm(data={})
        self.assertEqual(form.errors["name"][0], self.field_required_msg)
        self.assertEqual(form.errors["email"][0], self.field_required_msg)
        self.assertEqual(form.errors["residence"][0], self.field_required_msg)

    def test_order_form_is_invalid_for_missing_name_field(self):
        self.form_data.pop("name")
        form = OrderForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_order_form_is_invalid_for_missing_email_field(self):
        self.form_data.pop("email")
        form = OrderForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_order_form_is_invalid_for_missing_residence_field(self):
        self.form_data.pop("residence")
        form = OrderForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_order_form_name_is_cleaned_correctly(self):
        form = OrderForm(
            data={
                "name": "RoMiNa piStoLESI",
                "email": "romi@email.com",
                "residence": "AR",
            }
        )
        is_valid = form.is_valid()

        self.assertTrue(is_valid)
        self.assertEqual(form.cleaned_data["name"], "Romina Pistolesi")

    def test_order_form_email_is_cleaned_correctly(self):
        form = OrderForm(
            data={
                "name": "Romina Pistolesi",
                "email": "ROMINA@EMAIL.COM",
                "residence": "AR",
            }
        )
        is_valid = form.is_valid()

        self.assertTrue(is_valid)
        self.assertEqual(form.cleaned_data["email"], "romina@email.com")


class OrderSearchFormTests(TestCase):
    """
    Test suite to verify the order search form used to find an upcoming valid
    order works correctly.

    A user will use this form asking to resend an order confirmation email.
    """

    elements = [x[0] for x in OrderSearchForm.DOCUMENT_TYPE_CHOICES]

    def setUp(self):
        self.field_required_msg = "This field is required."
        self.form_data = {
            "document_type": fake.random_element(self.elements),
            "document_number": fake.passport_number(),
            "travel_date": fake.date_this_month(
                before_today=False, after_today=True
            ).strftime("%d-%m-%y"),
        }

    def test_form_is_valid_for_valid_data(self):
        form = OrderSearchForm(data=self.form_data)
        self.assertTrue(form.is_valid())


class PassengerFormTests(TestCase):
    """Test suite for Passenger model form"""

    def setUp(self):
        self.field_required_msg = "This field is required."
        self.form_data = {
            "document_type": fake.random_element(
                [x[0] for x in Passenger.DOCUMENT_TYPE_CHOICES if x[0]]
            ),
            "document_number": "95602823",
            "nationality": fake.random_element(countries)[0],
            "first_name": "GiSEla",
            "last_name": "vIdAl",
            "gender": fake.random_element(["F", "M"]),
            "birth_date": fake.date_of_birth(minimum_age=2, maximum_age=98).strftime(
                "%d/%m/%Y"
            ),
            "phone_number": "5491150254190",
        }

    def test_passenger_form_is_valid_for_valid_data(self):
        form = PassengerForm(data=self.form_data)

        self.assertTrue(form.is_valid())

    def test_empty_passenger_form_raises_valid_errors(self):
        form = PassengerForm(data={})
        self.assertEqual(form.errors["document_type"][0], self.field_required_msg)
        self.assertEqual(form.errors["document_number"][0], self.field_required_msg)
        self.assertEqual(form.errors["nationality"][0], self.field_required_msg)
        self.assertEqual(form.errors["first_name"][0], self.field_required_msg)
        self.assertEqual(form.errors["last_name"][0], self.field_required_msg)
        self.assertEqual(form.errors["gender"][0], self.field_required_msg)
        self.assertEqual(form.errors["birth_date"][0], self.field_required_msg)
        self.assertEqual(form.errors["phone_number"][0], self.field_required_msg)

    def test_passenger_form_is_invalid_for_missing_document_type_field(self):
        self.form_data.pop("document_type")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_document_number_field(self):
        self.form_data.pop("document_number")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_nationality_field(self):
        self.form_data.pop("nationality")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_first_name_field(self):
        self.form_data.pop("first_name")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_last_name_field(self):
        self.form_data.pop("last_name")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_gender_field(self):
        self.form_data.pop("gender")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_birth_date_field(self):
        self.form_data.pop("birth_date")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_is_invalid_for_missing_phone_number_field(self):
        self.form_data.pop("phone_number")
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())

    def test_passenger_form_first_name_is_cleaned_correctly(self):
        self.form_data["first_name"] = "giSeLa"
        form = PassengerForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["first_name"], "Gisela")

    def test_passenger_form_last_name_is_cleaned_correctly(self):
        self.form_data["last_name"] = "viDAL"
        form = PassengerForm(data=self.form_data)

        self.assertTrue(form.is_valid())

        self.assertEqual(form.cleaned_data["last_name"], "Vidal")

    def test_passenger_birth_date_cannot_be_in_the_future(self):
        self.form_data["birth_date"] = "01/01/2099"
        form = PassengerForm(data=self.form_data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["birth_date"][0],
            "Your birth date (2099-01-01) is invalid!",
        )
