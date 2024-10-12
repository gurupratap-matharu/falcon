import pdb
from importlib import import_module

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from selenium import webdriver
from selenium.webdriver.common.by import By

from orders.factories import OrderFactory, OrderItemFactory
from payments.views import PaymentView


class PaymentsFunctionalTests(StaticLiveServerTestCase):
    """
    Test suite to check that when a user has completed the order form he/she
    can see the payment options with correct pricing.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.Chrome()

    @classmethod
    def tearDownClass(cls):
        print("in tearDownClass...")
        cls.browser.quit()
        super().tearDownClass()

    @classmethod
    def create_session_store(cls):
        """Creates a database session store object that will contain the session key."""

        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        return store

    def test_payments_home_without_order_in_session_redirects_to_home(self):
        # Act
        # vicky directly tries to access the payments home url w/o placing an order
        self.browser.get(f"{self.live_server_url}{reverse('payments:home')}")

        # Assert

        # vicky should be redirected to home page
        self.assertIn("Ventanita", self.browser.title)
        self.assertEqual(
            self.browser.current_url, f"{self.live_server_url}{reverse('pages:home')}"
        )

        # she sees the alert message on top of the page
        alert = self.browser.find_element(By.CLASS_NAME, "alert-text")
        self.assertTrue(alert.is_displayed)
        self.assertEqual(alert.text, f"Info: {PaymentView.redirect_message}")

    def test_with_valid_order_user_can_see_all_payment_options(self):
        # Arrange
        self.order = OrderFactory(paid=False)
        self.order_item = OrderItemFactory(order=self.order)

        # here we add the key to the session in the DB
        session = self.create_session_store()
        session["order"] = str(self.order.id)
        session.save()
        # Now add the session key to the cookie that will be sent back to the server.
        cookie = {"name": settings.SESSION_COOKIE_NAME, "value": session.session_key}
        self.browser.add_cookie(cookie)
        # In pdb, do 'self.browser.get_cookies() to verify that it's there.'

        # vicky directly tries to access the payments url after placing order
        self.browser.get(f"{self.live_server_url}{reverse('payments:home')}")

        self.assertEqual(self.browser.title, "Payment | Ventanita")
