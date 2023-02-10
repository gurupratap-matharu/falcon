from django.test import SimpleTestCase

from orders.forms import OrderForm


class OrderFormTests(SimpleTestCase):
    """Test suite for order model form"""

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
