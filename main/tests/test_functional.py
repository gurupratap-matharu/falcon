from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By


class NewVisitorTest(StaticLiveServerTestCase):
    """
    Test suite to check a new visitor can access the site correctly.

    This is an E2E test with selenium to test our home page
    and its various elements.
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.browser = webdriver.Firefox()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.quit()
        super().tearDownClass()

    def test_can_search_for_a_trip(self):
        # Vicky has heard about a cool new bus ticket booking app. She goes to check out its homepage
        self.browser.get(f"{self.live_server_url}")

        # She notices the page title and header mention bus tickets
        self.assertIn("Falcon", self.browser.title)
        self.assertIn("Book Bus Tickets", self.browser.title)

        # She is invited to enter the origin, destination and journey date right away
        origin = self.browser.find_element(By.NAME, "origin")
        destination = self.browser.find_element(By.NAME, "destination")

        self.assertEqual(origin.get_attribute("placeholder"), "Search origin...")
        self.assertEqual(
            destination.get_attribute("placeholder"), "Search destination..."
        )

        origin_ac = self.browser.find_element(By.NAME, "autoComplete_list_1")

        destination_ac = self.browser.find_element(By.NAME, "autoComplete_list_2")

        # She types Bue (for buenos aires) in the origin box
        origin.send_keys("bue")

        # She should see the auto complete results
        self.assertTrue(origin_ac.is_displayed())

        # She types Men (for mendoza) in the destination box
        destination.send_keys("men")

        # She should see the auto complete results
        self.assertTrue(destination_ac.is_displayed())

        self.fail("Please finish the test!")

        # When she hits 'search' the page updates with relevant results showing buses available

        # Vicky wonders about...
        # how much luggage she can carry
        # whether the bus journey provides meals on board
        # how is the cancellation policy?
        # Then she notes that the site suggest a FAQ where most of her urgent queries are responded clearly
